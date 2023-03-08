import random
import math

from panda3d.core import Vec3
from panda3d.core import NodePath

from tree_specs import StemDefinition as sd
from tree_specs import Segment as sg


up = Vec3(0, 0, 1)


def print_definition_name(s):
    if sg.DEFINITION in s and sd.NAME in s[sg.DEFINITION]:
        print(s[sg.DEFINITION][sd.NAME])


def set_up_rng(s):
    if sg.RNG_SEED not in s:
        s[sg.RNG_SEED] = 0
    s[sg.RNG] = random.Random(s[sg.RNG_SEED])


def hierarchy(s):
    # On the tree's root, we need a NodePath that'll attach to the scene.
    if sg.TREE_ROOT not in s:
        s[sg.TREE_ROOT] = s
        s[sg.TREE_ROOT_NODE] = NodePath('tree_root')

    # If this is a new stem, set the administrative numbers.
    if sg.STEM_ROOT not in s:
        s[sg.STEM_ROOT] = s
        s[sg.REST_SEGMENTS] = s[sg.DEFINITION][sd.SEGMENTS] - 1
        s[sg.SPLIT_ACCUMULATOR] = 0.0

    s[sg.CONTINUATIONS] = []
    s[sg.BRANCHES] = []


def continuations(s):
    definition = s[sg.STEM_ROOT][sg.DEFINITION]
    segments = definition[sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    rng = s[sg.RNG]

    if rest_segments > 0: # Not the last segment?
        # How many splits do we have?
        if sd.SPLIT_CHANCE not in definition:
            splits = 0
        else:
            ratio = (segments - rest_segments) / segments
            accumulator = s[sg.STEM_ROOT][sg.SPLIT_ACCUMULATOR]
            split_chance_func = definition[sd.SPLIT_CHANCE]
            splits, accumulator = split_chance_func(ratio, accumulator, rng)
            s[sg.STEM_ROOT][sg.SPLIT_ACCUMULATOR] = accumulator

        if splits == 0:
            # Regular continuation
            s[sg.CONTINUATIONS].append(
                {
                    sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                    sg.TREE_ROOT: s[sg.TREE_ROOT],
                    sg.STEM_ROOT: s[sg.STEM_ROOT],
                    sg.PARENT_SEGMENT: s,
                    sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
                },
            )
        else:
            for idx in range(splits + 1):
                s[sg.CONTINUATIONS].append(
                    {
                        sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                        sg.TREE_ROOT: s[sg.TREE_ROOT],
                        sg.STEM_ROOT: s[sg.STEM_ROOT],
                        sg.PARENT_SEGMENT: s,
                        sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
                        sg.IS_NEW_SPLIT: (idx, splits + 1),
                    },
                )

    # Branch splits
    if sd.CHILD_DEFINITION in definition:
        age = s[sg.TREE_ROOT][sg.AGE]
        ratio = (segments - rest_segments - 0.5) / segments  # We measure density at mid-segment.
        branch_density_func = definition[sd.BRANCH_DENSITY]
        branch_density = branch_density_func(age, ratio, rng)
        for idx in range(math.floor(branch_density)):
            s[sg.CONTINUATIONS].append(
                {
                    sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                    sg.TREE_ROOT: s[sg.TREE_ROOT],
                    sg.PARENT_SEGMENT: s,
                    sg.IS_NEW_BRANCH: (idx + 1) / branch_density,
                    sg.DEFINITION: s[sg.STEM_ROOT][sg.DEFINITION][sd.CHILD_DEFINITION],
                },
            )


def length(s):
    if sg.TREE_ROOT_NODE in s:
        # On the tree's root, the tree's overall length is determined on the tree root.
        age = s[sg.TREE_ROOT][sg.AGE]
        length_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.LENGTH]
        rng = s[sg.RNG]

        length = length_func(age, 0, rng)
        s[sg.TREE_LENGTH] = length
        s[sg.STEM_LENGTH] = length
    elif sg.IS_NEW_BRANCH in s:
        # A branch's length is determined in relation to its parent.
        age = s[sg.TREE_ROOT][sg.AGE]
        length_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.LENGTH]
        rng = s[sg.RNG]
        parent_segments = s[sg.PARENT_SEGMENT][sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
        parent_offset = parent_segments - s[sg.PARENT_SEGMENT][sg.REST_SEGMENTS] + s[sg.IS_NEW_BRANCH] - 1
        parent_ratio = parent_offset / parent_segments

        length = length_func(age, parent_ratio, rng)
        s[sg.STEM_LENGTH] = length
        s[sg.BRANCH_RATIO] = parent_ratio

    # What is this stem's length per segment?
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    stem_length = s[sg.STEM_ROOT][sg.STEM_LENGTH]
    segment_legth = stem_length / segments

    s[sg.LENGTH] = segment_legth


def radius(s):
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    ratio = (segments - rest_segments) / segments
    radius_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.RADIUS]
    rng = s[sg.RNG]

    if sg.TREE_ROOT_NODE in s:  # Trunk of the tree
        s[sg.ROOT_RADIUS] = radius_func(age, 0, rng)

    s[sg.RADIUS] = radius_func(age, ratio, rng)


def attach_node(s):
    if sg.TREE_ROOT_NODE in s:  # Root of the tree
        parent_node = s[sg.TREE_ROOT_NODE]
    elif sg.IS_NEW_BRANCH in s:  # Root of the branch
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]

    node = parent_node.attach_new_node('tree_segment orientation')

    s[sg.NODE] = node


def split_curvature(s):
    if sg.IS_NEW_SPLIT in s:
        definition = s[sg.STEM_ROOT][sg.DEFINITION]
        split_idx, num_splits = s[sg.IS_NEW_SPLIT]
        age = s[sg.TREE_ROOT][sg.AGE]
        segments = definition[sd.SEGMENTS]
        rest_segments = s[sg.REST_SEGMENTS]
        ratio = (segments - rest_segments) / segments
        rng = s[sg.RNG]
        split_angle_func = definition[sd.SPLIT_ANGLE]
        node = s[sg.NODE]

        hpr = split_angle_func(age, ratio, split_idx, num_splits, rng)

        node.set_hpr(node.get_hpr() + hpr)


def branch_curvature(s):
    if sg.IS_NEW_BRANCH in s:
        age = s[sg.TREE_ROOT][sg.AGE]
        rng = s[sg.RNG]
        branch_ratio = s[sg.BRANCH_RATIO]
        branch_rotation_func = s[sg.DEFINITION][sd.BRANCH_ROTATION]
        branch_angle_func = s[sg.DEFINITION][sd.BRANCH_ANGLE]
        node = s[sg.NODE]
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
        length = s[sg.LENGTH] / s[sg.DEFINITION][sd.SEGMENTS]

        node.set_h(node.get_h() + branch_rotation_func(age, branch_ratio, rng))
        node.set_p(node.get_p() + branch_angle_func(age, branch_ratio, rng))
        node.set_pos(
            parent_node,
            0,
            0,
            -s[sg.PARENT_SEGMENT][sg.LENGTH] * (1.0 - s[sg.IS_NEW_BRANCH]),
        )


def bending(s):
    node = s[sg.NODE]
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    bending_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.BENDING]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]

    heading, pitch, roll = bending_func(age, ratio, rng)

    node.set_hpr(
        node.get_h() + heading / segments,
        node.get_p() + pitch / segments,
        node.get_r() + roll / segments,
    )


def design_tropism(s):
    node = s[sg.NODE]
    if sg.TREE_ROOT_NODE in s:
        parent_node = s[sg.TREE_ROOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    design_tropic_weight_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.DESIGN_TROPISM]
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]

    design_tropic_weight = design_tropic_weight_func(age, ratio, rng)

    s[sg.DESIGN_TWIST] = node.get_h()
    s[sg.DESIGN_TROPISM] = parent_node.get_relative_vector(node, up) * design_tropic_weight

    if sg.DEFINITION in s and sd.NAME in s[sg.DEFINITION]:
        print(s[sg.DESIGN_TROPISM])


def heliotropism(s):
    if sg.TREE_ROOT_NODE in s:
        parent_node = s[sg.TREE_ROOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    tree_root_node = s[sg.TREE_ROOT][sg.TREE_ROOT_NODE]
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]
    heliotropic_weight_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.HELIOTROPISM]
    global_heliotropic_direction = s[sg.TREE_ROOT][sg.HELIOTROPIC_DIRECTION]

    local_heliotropic_direction = parent_node.get_relative_vector(tree_root_node, global_heliotropic_direction)
    heliotropic_weight = heliotropic_weight_func(age, ratio, rng)

    s[sg.HELIOTROPISM] = local_heliotropic_direction * heliotropic_weight

    if sg.DEFINITION in s and sd.NAME in s[sg.DEFINITION]:
        print(s[sg.HELIOTROPISM])


def apply_tropisms(s):
    if sg.TREE_ROOT_NODE in s:
        parent_node = s[sg.TREE_ROOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    node = s[sg.NODE]
    length = s[sg.LENGTH]

    node.set_pos(0, 0, 0)
    node.set_hpr(0, 0, 0)

    design_twist = s[sg.DESIGN_TWIST]
    node.set_h(design_twist)

    total_tropism = s[sg.DESIGN_TROPISM] + s[sg.HELIOTROPISM]
    total_tropism = node.get_relative_vector(parent_node, total_tropism)
    total_tropism.normalize()
    pitch_tropism = Vec3(0, total_tropism.y, total_tropism.z)
    pitch_angle = pitch_tropism.angle_deg(Vec3(0, 0, 1))
    if pitch_tropism.y > 0.0:
        pitch_angle *= -1
    roll_angle = pitch_tropism.angle_deg(total_tropism)
    if total_tropism.x < 0.0:
        roll_angle *= -1

    node.set_p(pitch_angle)
    node.set_r(roll_angle)
    if sg.IS_NEW_BRANCH in s:
        node.set_pos(
            parent_node,
            0,
            0,
            -s[sg.PARENT_SEGMENT][sg.LENGTH] * (1.0 - s[sg.IS_NEW_BRANCH]),
        )
    #else:
    node.set_z(node, length)


def expand(s, tropisms=True):
    # Debug
    print_definition_name(s)
    # Segment logistics
    set_up_rng(s)
    hierarchy(s)
    continuations(s)
    # Segment visualization
    length(s)
    radius(s)
    # Design
    attach_node(s)
    split_curvature(s)
    branch_curvature(s)
    bending(s)
    # Tropisms
    if tropisms:
        design_tropism(s)
        heliotropism(s)
        apply_tropisms(s)
    else:
        s[sg.NODE].set_z(s[sg.NODE], s[sg.LENGTH])


def expand_fully(s, tropisms=True):
    segments = [s]
    while segments:
        segment = segments.pop()
        expand(segment, tropisms=tropisms)
        segments += segment[sg.CONTINUATIONS]
        segments += segment[sg.BRANCHES]
