import random
import math
import enum

from panda3d.core import Vec3
from panda3d.core import NodePath


def constant(value):
    def inner(_age, _ratio, _rng):
        return value
    return inner


def linear(v_from, v_to):
    def inner(_age, ratio, _rng):
        return v_from + (v_to - v_from) * ratio
    return inner


def noisy_linear_length(v_from, v_to, v_noise):
    def inner(age, ratio, rng):
        v = v_from + (v_to - v_from) * age
        v += rng.uniform(-1, 1) * v_noise
        return v
    return inner


def boring_radius(v_from, v_to):
    def inner(age, ratio, _rng):
        return (v_from + (v_to - v_from) * ratio) * age
    return inner


def func_curvature(pitch_func, curve_func):
    def inner(age, ratio, rng):
        return (pitch_func(age, ratio, rng), curve_func(age, ratio, rng))
    return inner


def s_curvature(lower_curve, higher_curve, variation, crumple, age_ratio):
    def inner(age, ratio, rng):
        if ratio <= 0.5:
            curve = lower_curve
        else:
            curve = higher_curve
        curve += rng.uniform(-1, 1) * variation

        pitch = rng.uniform(-1, 1) * crumple

        pitch *= age_ratio(age, ratio, rng)
        curve *= age_ratio(age, ratio, rng)
        return (pitch, curve)
    return inner


def linear_split_angle(angle_from, angle_to, angle_variation, age_ratio):
    def inner(age, ratio, rng):
         angle = angle_from + (angle_to - angle_from) * ratio
         angle += rng.uniform(-1, 1) * angle_variation
         angle *= age_ratio(age, ratio, rng)
         return angle
    return inner
    

def constant_splitting_func(chance):
    def inner(ratio, accumulator, rng):
        if rng.random() <= chance:
            splits = 1
        else:
            splits = 0
        return splits, accumulator
    return inner


def error_smoothing(split_chance_func):
    def inner(ratio, accumulator, rng):
        split_chance = split_chance_func(0, ratio, rng)
        split_chance_smoothed = split_chance + accumulator
        # We'll consider the number beore the decimal point as the
        # lower limit for the number of splits, and the one after it as
        # the chance for one more.
        bonus_split_chance = split_chance_smoothed % 1
        if rng.random() <= bonus_split_chance:
            splits = math.ceil(split_chance_smoothed)
        else:
            # Since a lot of negative error may have accumulated, we
            # need to take care not to wind up with a negative number of
            # splits.
            splits = max(0, math.floor(split_chance_smoothed))

        error_correction = splits - split_chance
        accumulator -= error_correction

        return splits, accumulator
    return inner


def branch_density(ratio_func):
    def inner(age, ratio, rng):
        return ratio_func(age, ratio, rng)
    return inner


def branch_length_function(ratio_func):
    def inner(age, ratio, rng):
        return ratio_func(age, ratio, rng)
    return inner
    

class StemType(enum.Enum):
    STEM = 1
    LEAF = 2


class StemCurvature(enum.Enum):
    SINGLE = 1
    DOUBLE = 2


class StemDefinition(enum.Enum):
    NAME             = 99
    SEGMENTS         =  1  # Number of segments in the stem.
    LENGTH           =  2  # age -> length of the stem
    RADIUS           =  3  # age, ratio along stem length -> diameter
    BENDING          =  4  # age, ratio along stem length -> pitch, roll
    SPLIT_CHANCE     =  5  # ratio, accumlator -> chance, accumlator
    SPLIT_ANGLE      =  6
    CHILD_DEFINITION =  7  # StemDefinition of the next level of branches
    BRANCH_DENSITY   =  8
    BRANCH_ANGLE     =  9  # Pitch angle at which a branch splits off, uses branch point ratio along parent stem
    BRANCH_ROTATION  = 10  # Heading for the same.
    HELIOTROPISM     = 11


class Segment(enum.Enum):
    # Administrative
    RNG_SEED              =  1  # Seed for the random number generator.
    RNG                   =  2  # The random nnumber generator itself.
    DEFINITION            =  3  # The StemDefinition for this stem.
    # Parameters
    AGE                   =  4
    HELIOTROPIC_DIRECTION =  5
    # Segment hierarchy
    TREE_ROOT             =  6  # The first segment of the tree.
    STEM_ROOT             =  7  # The first segment of the stem.
    CONTINUATIONS         =  8  # Segments that continue the stem.
    BRANCHES              =  9
    PARENT_SEGMENT        = 10  # The segment from which this one sprouts.
    REST_SEGMENTS         = 11  # The number of segments left in the stem, inluding this one.
    # Node hierarchy
    TREE_ROOT_NODE        = 12  # The NodePath representing the tree's starting point.
    FOOT_NODE             = 13
    LENGTH_NODE           = 14  # A NodePath raise along a segment's length, in zero orientation
    NODE                  = 15  # The NodePath attached to the LENGTH_NODE, used solely for orientation
    # Geometry data
    TREE_LENGTH           = 16
    STEM_LENGTH           = 17
    LENGTH                = 18  # Length of the segment
    RADIUS                = 19  # The segment's radius ad the top.
    ROOT_RADIUS           = 20  # Trunk radius at the root node (ratio = 0), present only on the TREE_ROOT
    # Stem splitting
    IS_NEW_SPLIT          = 21  # Is this segment created through stem splitting?
    SPLIT_ACCUMULATOR     = 22  # Rounding error accumulator for splitting; Stored on the stem's root.
    # CLONE_BENDING_DEBT  = 12  # Curvature from a split that needs to be compensated for
    # Branching
    IS_NEW_BRANCH         = 23  # FIXME: Is the ratio along the parent segment
    BRANCH_RATIO          = 24  # Ratio along parent stem where the branch is attached
    # Tropism
    DESIGN_TROPISM        = 25
    HELIOTROPISM          = 26  # 


sc = StemCurvature
sd = StemDefinition
sg = Segment


# FIXME: Move to species definitions file
BoringWillowish = {
    # sd.NAME: "Willowish Trunk",
    sd.SEGMENTS: 10,
    sd.LENGTH: noisy_linear_length(1, 8, 0),
    sd.RADIUS: boring_radius(0.5, 0.1),
    sd.BENDING: s_curvature(
        45,                # Lower curvature
        -60,               # Higher curvature
        600,               # Curvature noisiness
        600,               # Noisiness along the other axis
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
    sd.SPLIT_CHANCE: error_smoothing(constant(0.1)),
    sd.SPLIT_ANGLE: linear_split_angle(
        60,
        30,
        10,
        linear(0.8, 1.0),
    ),
    sd.BRANCH_DENSITY: branch_density(linear(10.5, 0.5)),  #constant(20.0)),
    sd.HELIOTROPISM: constant(0.0),
    sd.CHILD_DEFINITION: {
        # sd.NAME: "Willowish Branch",
        sd.SEGMENTS: 5,
        sd.LENGTH: branch_length_function(linear(2.0, 3.0)),
        sd.BRANCH_ANGLE: linear(90.0, 30.0),
        sd.BRANCH_ROTATION: noisy_linear_length(0.0, 0.0, 180.0),
        sd.RADIUS: constant(0.04),
        sd.BENDING: func_curvature(constant(0.0), constant(0.0)),
        sd.HELIOTROPISM: constant(0.3),
    },
}

BoringFirish = {
    sd.NAME: "Firish Trunk",
    sd.SEGMENTS: 10,
    sd.LENGTH: noisy_linear_length(1, 8, 0),
    sd.RADIUS: boring_radius(0.3, 0.1),
    sd.BENDING: s_curvature(
        0,                 # Lower curvature
        0,                 # Higher curvature
        10,                # Curvature noisiness
        10,                # Noisiness along the other axis
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
    sd.BRANCH_DENSITY: branch_density(linear(10.5, 0.5)),  #constant(20.0)),
    sd.CHILD_DEFINITION: {
        # sd.NAME: "Firish Branch",
        sd.SEGMENTS: 1,
        sd.LENGTH: branch_length_function(linear(3.0, 1.0)),
        sd.BRANCH_ANGLE: linear(90.0, 30.0),
        sd.BRANCH_ROTATION: noisy_linear_length(0.0, 0.0, 180.0),
        sd.RADIUS: constant(0.04),
        sd.BENDING: func_curvature(constant(0.0), constant(0.0)),
    },
}

BoringBoringish = {
    sd.NAME: "Trunk",
    sd.SEGMENTS: 2,
    sd.LENGTH: noisy_linear_length(1, 8, 0),
    sd.RADIUS: boring_radius(0.3, 0.1),
    sd.BENDING: s_curvature(
        0,                 # Lower curvature
        0,                 # Higher curvature
        0,                 # Curvature noisiness
        0,                 # Noisiness along the other axis
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
}


BoringTree = BoringWillowish
#BoringTree = BoringFirish
#BoringTree = BoringBoringish


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


def attach_node(s):
    if sg.TREE_ROOT_NODE in s:  # Root of the tree
        parent_node = s[sg.TREE_ROOT_NODE]
    elif sg.IS_NEW_BRANCH in s:  # Root of the branch
        parent_node = s[sg.PARENT_SEGMENT][sg.FOOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    foot_node = parent_node.attach_new_node('tree_segment foot')
    length_node = foot_node.attach_new_node('tree_segment length')
    node = length_node.attach_new_node('tree_segment orientation')
    s[sg.FOOT_NODE] = foot_node
    s[sg.LENGTH_NODE] = length_node
    s[sg.NODE] = node


def split_curvature(s):
    if sg.IS_NEW_SPLIT in s:
        heading = s[sg.RNG].uniform(-1, 1) * 180.0

        definition = s[sg.STEM_ROOT][sg.DEFINITION]
        age = s[sg.TREE_ROOT][sg.AGE]
        segments = definition[sd.SEGMENTS]
        rest_segments = s[sg.REST_SEGMENTS]
        ratio = (segments - rest_segments) / segments
        rng = s[sg.RNG]
        split_angle_func = definition[sd.SPLIT_ANGLE]
        node = s[sg.FOOT_NODE]

        split_angle = split_angle_func(age, ratio, rng)

        node.set_p(node.get_p() - split_angle)
        node.set_h(node.get_h() + heading)


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

    node = s[sg.LENGTH_NODE]
    node.set_z(segment_legth)
    s[sg.LENGTH] = segment_legth


def branch_curvature(s):
    if sg.IS_NEW_BRANCH in s:
        age = s[sg.TREE_ROOT][sg.AGE]
        rng = s[sg.RNG]
        branch_ratio = s[sg.BRANCH_RATIO]
        node = s[sg.FOOT_NODE]
        branch_rotation_func = s[sg.DEFINITION][sd.BRANCH_ROTATION]
        branch_angle_func = s[sg.DEFINITION][sd.BRANCH_ANGLE]

        node.set_h(node.get_h() + branch_rotation_func(age, branch_ratio, rng))
        node.set_p(node.get_p() + branch_angle_func(age, branch_ratio, rng))
        node.set_z(node.get_z() + s[sg.PARENT_SEGMENT][sg.LENGTH] * s[sg.IS_NEW_BRANCH])


def continuations(s):
    definition = s[sg.STEM_ROOT][sg.DEFINITION]
    segments = definition[sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    rng = s[sg.RNG]

    if rest_segments > 0: # Not the last segment?
        # Regular continuations
        s[sg.CONTINUATIONS].append(
            {
                sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                sg.TREE_ROOT: s[sg.TREE_ROOT],
                sg.STEM_ROOT: s[sg.STEM_ROOT],
                sg.PARENT_SEGMENT: s,
                sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
            },
        )

        # Stem splits
        if sd.SPLIT_CHANCE in definition:
            ratio = (segments - rest_segments) / segments
            accumulator = s[sg.STEM_ROOT][sg.SPLIT_ACCUMULATOR]
            split_chance_func = definition[sd.SPLIT_CHANCE]
            splits, accumulator = split_chance_func(ratio, accumulator, rng)
    
            s[sg.STEM_ROOT][sg.SPLIT_ACCUMULATOR] = accumulator
            for idx in range(splits):
                s[sg.CONTINUATIONS].append(
                    {
                        sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                        sg.TREE_ROOT: s[sg.TREE_ROOT],
                        sg.STEM_ROOT: s[sg.STEM_ROOT],
                        sg.PARENT_SEGMENT: s,
                        sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
                        sg.IS_NEW_SPLIT: True,
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


def bending(s):
    node = s[sg.FOOT_NODE]
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    bending_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.BENDING]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]

    pitch, roll = bending_func(age, ratio, rng)

    node.set_hpr(
        node.get_h() + 0,
        node.get_p() + pitch / segments,
        node.get_r() + roll / segments,
    )


def design_tropism(s):
    node = s[sg.NODE]
    if sg.TREE_ROOT_NODE in s:
        parent_node = s[sg.TREE_ROOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]

    s[sg.DESIGN_TROPISM] = parent_node.get_relative_vector(node, up)


def heliotropism(s):
    node = s[sg.NODE]
    tree_root_node = s[sg.TREE_ROOT][sg.TREE_ROOT_NODE]
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]
    heliotropic_weight_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.HELIOTROPISM]
    global_heliotropic_direction = s[sg.TREE_ROOT][sg.HELIOTROPIC_DIRECTION]

    local_heliotropic_direction = node.get_relative_vector(tree_root_node, global_heliotropic_direction)
    heliotropic_weight = heliotropic_weight_func(age, ratio, rng)

    s[sg.HELIOTROPISM] = local_heliotropic_direction * heliotropic_weight


def apply_tropisms(s):
    foot_node = s[sg.FOOT_NODE]
    length_node = s[sg.LENGTH_NODE]
    node = s[sg.NODE]
    length = s[sg.LENGTH]

    total_tropism = s[sg.DESIGN_TROPISM] + s[sg.HELIOTROPISM]
    pitch_tropism = Vec3(0, total_tropism.y, total_tropism.z)
    pitch_angle = pitch_tropism.angle_deg(Vec3(0, 0, 1))
    if pitch_tropism.y > 0.0:
        pitch_angle *= -1
    roll_angle = pitch_tropism.angle_deg(total_tropism)
    if total_tropism.x < 0.0:
        roll_angle *= -1

    foot_node.set_pos(0, 0, 0)
    foot_node.set_hpr(0, 0, 0)
    length_node.set_pos(0, 0, 0)
    length_node.set_hpr(0, 0, 0)
    node.set_pos(0, 0, 0)
    node.set_hpr(0, 0, 0)

    foot_node.set_p(pitch_angle)
    foot_node.set_r(roll_angle)
    #foot_node.set_h(foot_node, -heading_angle)
    length_node.set_z(length)


def expand(s, tropisms=True):
    # Debug
    print_definition_name(s)
    set_up_rng(s)
    hierarchy(s)
    attach_node(s)
    split_curvature(s)
    length(s)
    branch_curvature(s)
    radius(s)
    bending(s)
    continuations(s)
    # Tropisms
    if tropisms:
        design_tropism(s)
        heliotropism(s)
        apply_tropisms(s)


def expand_fully(s, tropisms=True):
    segments = [s]
    while segments:
        segment = segments.pop()
        expand(segment, tropisms=tropisms)
        segments += segment[sg.CONTINUATIONS]
        segments += segment[sg.BRANCHES]


###
### PRE-REFACTOR
###

# # 4.3 Stem children
# #
# # nBranches: maximum number of child sub-stems that a stem can create over all of its segments.
# # The actual number of children from any stem might be less than this maximum.
# #
# # Any stem that has been cloned or is, itself, a clone reduces its propensity to form clones by half.
# # The function ShapeRatio(shape, ratio):
# #   Shape                    Result
# #   0 (conical)              0.2 + 0.8 * ratio
# #   1 (spherical)            0.2 + 0.8 * sin(pi * ratio)
# #   2 (hemispherical)        0.2 + 0.8 * sin(0.5 * pi * ratio)
# #   3 (cylindrical)          1.0
# #   4 (tapered cylindrical)  0.5 + 0.5 * ratio
# #   5 (flame)                ratio <= 0.7: ratio / 0.7
# #                            else        : (1.0 - ratio) / 0.3
# #   6 (inverse conical)      1.0 - 0.8 * ratio
# #   7 (tend flame)           ratio <= 0.7: 0.5 + 0.5 * ratio / 0.7
# #                            else        : 0.5 + 0.5 * (1.0 - ratio) / 0.3
# #   8 (envelope)             use pruning envelope (see Section 4.6)
# #
# # 
# #   length_child_max = nLength ± nLengthV  # The maximum relative length as a fraction of its parent's specific length
# #   offset_child = the position in meters of the child along the parent's length (from the base).
# #   # The number of successive child stems (really "grandchildren") is computed as
# #   for the first level of branches:
# #     stems = stems_max * (0.2 + 0.8 * (length_child / length_parent) / length_child_max)
# #   further levels of branches
# #     stems = stems_max * (1.0 - 0.5 * (offset_child / length_parent))
# #   scale_tree = Scale ± ScaleV
# #   length_base = fractional bare area at the base of the tree calculated as (BaseSize * scale_tree)
# #   length_trunk = (0Length ± 0LengthV) * scale_tree
# #   if first_level_of_branches:
# #     length_child = length_trunk * length_child_max * ShapeRatio((Shape, (length_trunk-offset_child)/(length_trunk - length_base))
# #   else:
# #     length_child = length_child_max * ( length_parent - 0.6 * offset_child)
# #   # the z-axis of a child rotates away from the z-axis of its parent about the x-axis at an angle of:
# #   if nDownAngleV >= 0.0:
# #     downangle_child = nDownAngle ± nDownAngleV
# #   else:
# #     downangle_child = nDownAngle ± abs(nDownAngleV * (1 - 2 * conical((length_parent - offset_child) / (length_parent - length_base))))
# #
# # This can be used to linearly change the down angle based on the position of the child along its parent, as with the Black Tupelo's main branches
# # seen in Plate 2b. Note how they are angled upward near the crown of the tree and angled downward near the bottom.
# 
# # Transformations applied to stem segments:
# # * bend / bend_back
# # * Split angles and split angle debt
# # * Rotation around tree z 
# # * Light attraction
# # * (RotateV seems implied by diagram)
# 
# # Transformations applied to stem children:
# # * nDownAngleV
# # * nRotate
# 
# 
# 
# # To generate animation:
# # * build a Character with the entire joint hierarchy
# # * put a TransformBlendTable on your geometry to map vertices to joints
# # * each animation would require an AnimBundle that replicates the
# #   Character's joint hierarchy and specifies a transform for each joint
# #   each frame of the animation
# 
# # Missing:
# # * Helical stems when nCurveBack < 0
# 
# class StemletSheet:
#     def __init__(self, tree_root_node, root_node=None, rest_segments=None, root_length=0.0, branch_definition=BoringTree, rng=0, splitting_acc=0.0,
#                  child_rotate_acc=0.0, bend_debt=0.0, style=Skeleton, children=None, branching_weight=1.0, stem_length=None, stem_diameter=None,
#                  fecundity=1.0,
#     ):
#         """
#         tree_root_node
#             NodePath of the root of the whole tree
#         root_node
#             The previous segment's NodePath. Defaults to tree_root_node
#         children
#             Sheets generated by this sheet.
#         rest_segments
#             Number of segments left to create in this stem. Defaults to
#             the number of segments in branch_definition.
#         root_length
#             The previous segment's length. Defaults to 0.0
#         branch_definition
#             The tree class. Defaults to :class:`BoringTree`
#         rng
#             Random seed to use for the next segment. Defaults to 0
#         splitting_acc
#             Accumulated error for Floyd-Steinberg-ish error diffusion of
#             stem split angles. Defaults to 0.0
#         child_rotate_acc
#             Accumulated rotation of stem child segments
#         bend_debt
#             bending accumulated through splits, the inverse of which is
#             distributed over the rest of the stem, bending it back
#             towards the original stem's direction.
#         branching_weight
#             The sheet's weight in the random choice of the distribution
#             of a branch level's children.
#         style
#             Style specification with parameters for geometry generation.
#         stem_length
#             Total length of the stem.
#         stem_diameter
#             Basic untapered diameter of the stem.
#         fecundity
#             Propensity to form branches. Each stem split divides the
#             fecundity by the number of splits
#         """
#         if rest_segments is None:
#             rest_segments = branch_definition.segments
#         if root_node is None:
#             root_node = tree_root_node
#         if children is None:
#             children = []
# 
#         # Related nodes and sheets
#         self.tree_root_node = tree_root_node
#         self.root_node = root_node
#         self.children = children
# 
#         # Global data
#         self.style = style
# 
#         # Stem data
#         self.branch_definition = branch_definition
#         self.stem_length = stem_length
#         self.stem_diameter = stem_diameter
# 
#         # Stemlet data
#         self.rng = rng
#         self.rest_segments = rest_segments
#         self.root_length = root_length
#         self.splitting_acc = splitting_acc
#         self.child_rotate_acc = child_rotate_acc
#         self.bend_debt = bend_debt
#         self.branching_weight = branching_weight
#         self.fecundity = fecundity
# 
# 
# def stemletify(sheet):
#     segment_type = sheet.branch_definition.segment_type
#     if segment_type == SegmentType.STEM:
#         return stemify(sheet)
#     elif segment_type == SegmentType.LEAF:
#         model = loader.load_model("models/smiley")
#         model.reparent_to(sheet.root_node)
#         model.set_scale(0.5)
#         return []
#     else:
#         raise ValueError("Unknown segment_type {}".format(segment_type))
# 
# 
# def stemify(sheet):
#     """
#     Takes a stemlet sheet, attaches relevant scene subgraphs to the 
#     sheet's node, and returns a list of sheets for the next segments
#     in this S-stem (continuation and possible split clones), and
#     branches.
#     """
#     bd = sheet.branch_definition
#     child_sheets = []  # dictionaries for StemletSheet kwargs. Can't finalize them
#                        # until the rotation of all children has been accumulated.
# 
#     slrng = random.Random(sheet.rng)  # stemlet rng
# 
#     # The stem's first segment has no clones. The second might be a
#     # splitting trunk, or a regularly cloning segment as all those to
#     # come.
#     if (bd.segments == sheet.rest_segments):
#         splits_base = 0
#     elif (bd.segments - 1 == sheet.rest_segments) and bd.trunk_splits:
#         splits_base = bd.trunk_splits
#     else:
#         splits_base = bd.splits
# 
#     # Floyd-Steinberg-ishly diffused splitting determination
#     splitting_acc = sheet.splitting_acc
#     if slrng.random() <= (splits_base - math.floor(splits_base)) + splitting_acc:
#         splits = math.floor(splits_base) + 1
#     else:
#         splits = math.floor(splits_base)
#     splitting_acc -= splits - splits_base
# 
#     fecundity = sheet.fecundity / (splits + 1)
# 
#     # Create stem segments
#     for split_idx in range(splits + 1):
#         # Create stemlet node
#         gdrng = random.Random(slrng.random())  # geometry data rng
#         node = sheet.root_node.attach_new_node('stemlet')
#         node.set_z(sheet.root_length)  # position at the end of the parent
# 
#         # Segment length. If this is the tree's root, the trunk's length has to be determined.
#         if sheet.stem_length is None:
#             sheet.stem_length = bd.length + gdrng.uniform(-1, 1) * bd.length_var
#         stemlet_length = sheet.stem_length / bd.segments
# 
#         # Same goes for diameter.
#         if sheet.stem_diameter is None:
#             sheet.stem_diameter = bd.diameter + gdrng.uniform(-1, 1) * bd.diameter_var
# 
#         # Basic bend and split angle back bend: stemlet_bend, stemlet_debt_repayed
#         if not bd.bend_back:
#             stemlet_bend = bd.bend / bd.segments + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
#         else:
#             is_lower_half = sheet.rest_segments <= bd.segments / 2
#             if is_lower_half:
#                 stemlet_bend = bd.bend / (bd.segments / 2) + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
#             else:
#                 stemlet_bend = -bd.bend_back / (bd.segments / 2) + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
#         stemlet_debt_repayed = sheet.bend_debt / sheet.rest_segments
#         stemlet_bend -= stemlet_debt_repayed
#         node.set_p(node, stemlet_bend)
# 
#         # Upward / Light attraction
#         up = Vec3(0, 0, 1)
#         local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, up)
#         upward_angle = 0.0 - math.asin(local_tree_up.y) / (2.0 * math.pi) * 360.0 
# 
#         # forward = Vec3(0, 1, 0)
#         # local_tree_forward = sheet.root_node.get_relative_vector(sheet.tree_root_node, forward)
#         # orientation = math.acos(local_tree_forward.z)
#         attraction_up = upward_angle / sheet.rest_segments * bd.upward_attraction
#         node.set_p(node, + attraction_up)
#         
#         # Split angle
#         if split_idx > 0:
#             up = Vec3(0, 0, 1)
#             local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, up)
#             declination = local_tree_up.angle_deg(up)
#             split_angle = max(bd.split_angle + gdrng.uniform(-1, 1) * bd.split_angle_var - declination, 0)
#         else:
#             split_angle = 0.0
#         node.set_p(node, split_angle)
# 
#         # Split rotation around tree's z
#         if split_idx > 0: # FIXME: ...in contradiction to the paper
#             local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, Vec3(0, 0, 1))
#             declination = math.acos(local_tree_up.z) / math.pi * 360.0
#             angle_magnitude = 20 + 0.75 * (30 + abs(declination - 90)) * gdrng.random() ** 2
#             stemlet_z_rotation = angle_magnitude * gdrng.choice([-1, 1]) * bd.split_tree_z
#         else:
#             stemlet_z_rotation = 0.0
#         node.set_hpr(
#             node,
#             node.get_relative_vector(
#                 sheet.tree_root_node,
#                 Vec3(stemlet_z_rotation, 0, 0),
#             ),
#         )
# 
#         ### Stem children
#         # Children only occur above the stem's base
#         offset = (bd.segments - (sheet.rest_segments - 1)) / bd.segments
#         child_rotate_acc = sheet.child_rotate_acc
#         if (bd.child_definition is not None) and (offset > bd.length_base):
#             if bd.shape is not None:  # Branches on the trunk
#                 stems = bd.child_branches / bd.segments * (0.2 + 0.8 * offset) * fecundity
#             else:  # Branches on branches
#                 stems = bd.child_branches / bd.segments * (1.0 - 0.5 * offset) * fecundity
#             # print(fecundity, offset, stems)
#             children = math.floor(stems)            
#             if random.random() <= stems % 1:
#                 children += 1
# 
#             # Child length is determined using the Shape function
#             offset_without_base = min(1, (1 - offset) / (1 - bd.length_base))
#             if bd.shape is not None:  # Trunk uses different function...
#                 child_scale = bd.shape(offset_without_base)
#             else:
#                 child_scale = 1 - 0.6 * offset
#             child_length = sheet.stem_length * child_scale * bd.child_scale
# 
#             # Child branch diameter
#             child_diameter = sheet.stem_diameter * (child_length / sheet.stem_length) ** bd.child_diameter_power
# 
#             for child_idx in range(children):
#                 child_node = node.attach_new_node('child')
# 
#                 # Place at segment's end
#                 child_node.set_pos(0, 0, stemlet_length)
#     
#                 # Rotate around the parent's Z (nRotate +/- nRotateV)
#                 if bd.child_rotate_mode == SplitRotation.HELICAL:
#                     child_rotate_acc += bd.child_rotate + gdrng.uniform(-1, 1) * bd.child_rotate_var
#                 elif bd.child_rotate_mode == SplitRotation.COPLANAR:
#                     child_rotate_acc += -bd.child_rotate + gdrng.uniform(-1, 1) * bd.child_rotate_var + 180
#                 else:
#                     raise ValueError("Unknown child_rotate_mode {}".format(bd.child_rotate_mode))
#                 child_rotate_acc = child_rotate_acc % 360
#                 child_node.set_h(child_rotate_acc)
# 
#                 # nDownAngle
#                 if bd.child_down >= 0:
#                     down_angle = bd.child_down + gdrng.uniform(-1, 1) * bd.child_down_var
#                 else:
#                     raise Exception
#                     # down_angle = bd.child_down +- abs(bd.child_down_var * (1 - 2 * conical(lengthparent - offsetchild) / (lengthparent - lengthbase)))
#                 child_node.set_p(down_angle)
# 
#                 # Upward attraction (copypasted from above)
#                 up = Vec3(0, 0, 1)
#                 local_tree_up = node.get_relative_vector(sheet.tree_root_node, up)
#                 upward_angle = 0.0 - math.asin(local_tree_up.y) / (2.0 * math.pi) * 360.0 
#                 attraction_up = upward_angle / bd.child_definition.segments * bd.upward_attraction
#                 child_node.set_p(child_node, attraction_up)
# 
#                 # ...and create the child's sheet.
#                 child_sheet = StemletSheet(
#                     tree_root_node   =sheet.tree_root_node,
#                     root_node        =child_node,
#                     branch_definition=bd.child_definition,
#                     rng              =slrng.random(),
#                     style            =sheet.style,
#                     stem_length      =child_length,
#                     stem_diameter    =child_diameter,
#                     fecundity        =fecundity,
#                 )
#                 child_sheets.append(child_sheet)
# 
#         ### Stem-continuing sheet
#         if sheet.rest_segments > 1:
#             child_sheet = StemletSheet(
#                 tree_root_node   =sheet.tree_root_node,
#                 root_node        =node,
#                 rest_segments    =sheet.rest_segments - 1,
#                 root_length      =stemlet_length,
#                 branch_definition=bd,
#                 rng              =slrng.random(),
#                 splitting_acc    =splitting_acc,
#                 bend_debt        =sheet.bend_debt - stemlet_debt_repayed + split_angle,
#                 child_rotate_acc =child_rotate_acc,
#                 style            =sheet.style,
#                 stem_length      =sheet.stem_length,
#                 stem_diameter    =sheet.stem_diameter,
#                 branching_weight =sheet.branching_weight / (splits + 1),
#                 fecundity        =fecundity,
#             )
#             child_sheets.append(child_sheet)
# 
#         ### Graphics-related stuff
# 
#         # Stem diameter
#         if bd.segment_type == SegmentType.STEM:
#             # Basic taper
#             runlength = 1 - (sheet.rest_segments + 1) / (bd.segments + 1)  # Z
#             if bd.taper <= 1:
#                 unit_taper = bd.taper
#             elif 1 < bd.taper <= 2:
#                 unit_taper = 2 - bd.taper
#             else:
#                 unit_taper = 0
#             taper_z = sheet.stem_diameter * (1 - unit_taper * runlength)  # taper_z_top = 1 - (sheet.rest_segments) / (bd.segments + 1)
#             if bd.taper < 1:
#                 stemlet_diameter = taper_z
#             else:
#                 Z_2 = (1 - runlength) * sheet.stem_length
#                 if bd.taper < 2 or Z_2 < taper_z:
#                     depth = 1
#                 else:
#                     depth = bd.taper - 2
#                 if bd.taper < 2:
#                     Z_3 = Z_2
#                 else:
#                     Z_3 = abs(Z_2 - 2 * taper_z * int(Z_2 / (2 * taper_z) + 0.5))
#                 if bd.taper < 2 and Z_3 >= taper_z:
#                     stemlet_diameter = taper_z
#                 else:
#                     stemlet_diameter = (1 - depth) * taper_z + depth * math.sqrt(taper_z ** 2 - (Z_3 - taper_z) ** 2)
#             # Flare
#             stemlet_diameter *= bd.flare * (100 ** (1 - 8 * runlength) - 1) / 100 + 1
#         
#     return child_sheets
# 
# 
# def treeify(root, bd, rng, style=Skeleton):
#     """
#     Attach a (botanical) tree's geometry to a NodePath.
# 
#     root
#         NodePath to add tree to
#     bd
#         Stem definition
#     rng
#         :class:`random.Random` seed
# 
#     style
#         Style definition to use for geometry
#     """
#     def expand(sheets):
#         new_sheets = []
#         while sheets:
#             sheet = sheets.pop()
#             children = stemletify(sheet)
#             sheet.children = children
#             sheets += children
#             new_sheets += children
#         return new_sheets
#     
#     root_sheet = Stem(
#         tree_root=root,
#         branch_definition=bd,
#         rng=random.random(),
#         style=style,
#     )
# 
#     # First expansion pass
#     sheets = [root_sheet]
#     new_sheets = expand(sheets)
#     # import pdb; pdb.set_trace()
