import random
import math
import enum

from panda3d.core import Vec3
from panda3d.core import NodePath


def constant(value):
    def inner(r):
        return value
    return inner


def linear(v_from, v_to):
    def inner(r):
        return v_from + (v_to - v_from) * r
    return inner


def noisy_linear(v_from, v_to, v_noise):
    def inner(r, rng):
        return v_from + (v_to - v_from) * r + rng.uniform(-1, 1) * v_noise
    return inner


def boring_radius(v_from, v_to):
    def inner(age, r, _rng):
        return (v_from + (v_to - v_from) * r) * age
    return inner


def s_curvature(lower_curve, higher_curve, variation, crumple, age_ratio):
    def inner(age, trunk_ratio, rng):
        if trunk_ratio <= 0.5:
            curve = lower_curve
        else:
            curve = higher_curve
        curve += rng.uniform(-1, 1) * variation

        pitch = rng.uniform(-1, 1) * crumple
        return (pitch * age_ratio(age), curve * age_ratio(age))
    return inner


class StemType(enum.Enum):
    STEM = 1
    LEAF = 2


class StemCurvature(enum.Enum):
    SINGLE = 1
    DOUBLE = 2


class StemDefinition(enum.Enum):
    SEGMENTS       =  1  # Number of segments in the stem.
    LENGTH         =  2  # age -> length of the stem
    RADIUS         =  3  # age, ratio along stem length -> diameter
    BENDING        =  4  # age, ratio along stem length -> pitch, roll
    STEM_SPLITS    =  5
    BASE_SPLITS    =  6


class Segment(enum.Enum):
    # Administrative
    RNG_SEED           =  1  # Seed for the random number generator.
    RNG                =  2  # The random nnumber generator itself.
    DEFINITION         =  3  # The StemDefinition for this stem.
    # Parameters
    AGE                =  4
    # Segment hierarchy
    TREE_ROOT          =  5  # The first segment of the tree.
    STEM_ROOT          =  6  # The first segment of the stem.
    CONTINUATIONS      =  7  # Segments that continue the stem.
    PARENT_SEGMENT     =  8  # The segment from which this one sprouts.
    REST_SEGMENTS      =  9  # The number of segments left in the stem, inluding this one.
    # Node hierarchy
    TREE_ROOT_NODE     = 10  # The NodePath representing the tree's starting point.
    LENGTH_NODE        = 11  # A NodePath raise along a segment's length, in zero orientation
    NODE               = 12  # The NodePath attached to the LENGTH_NODE, used solely for orientation
    # Geometry data
    LENGTH             = 13  # Length of the segment
    RADIUS             = 14  # The segment's radius ad the top.
    ROOT_RADIUS        = 15  # Trunk radius at the root node (ratio = 0), present only on the TREE_ROOT
    # SPLITTING_ACC      = 10  # Rounding error accumulator for splitting; Stored on the stem's root.
    # IS_NEW_CLONE       = 11  # Is this segment created through stem splitting?
    # CLONE_BENDING_DEBT = 12  # Curvature from a split that needs to be compensated for


sc = StemCurvature
sd = StemDefinition
sg = Segment


# FIXME: Move to species definitions file
BoringTree = {
    sd.SEGMENTS: 10,
    sd.LENGTH: noisy_linear(1, 8, 0),
    sd.RADIUS: boring_radius(0.5, 0.3),
    sd.BENDING: s_curvature(
        45,                # Lower curvature
        -60,               # Higher curvature
        135,               # Curvature noisiness
        135,               # Noisiness along the other axis
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
    # sd.CLONES: 0.0,
    # sd.BASE_CLONES: 1.5,
    # sd.SPLIT: 80.0,
    # sd.SPLIT_VAR: 30.0,
    # sd.SPLIT_ROTATION: 90.0,
}


up = Vec3(0, 0, 1)


# set_up_rng
#   RNG_SEED (defaults to 0 if not present) -> RNG
# hierarchy

def set_up_rng(s):
    if sg.RNG_SEED not in s:
        s[sg.RNG_SEED] = 0
    if sg.RNG not in s:
        s[sg.RNG] = random.Random(s[sg.RNG_SEED])


def hierarchy(s):
    if sg.TREE_ROOT not in s:
        s[sg.TREE_ROOT] = s
        s[sg.TREE_ROOT_NODE] = NodePath('tree_root')

    # If this is a new stem, set the administrative numbers.
    if sg.STEM_ROOT not in s:
        s[sg.STEM_ROOT] = s
        s[sg.REST_SEGMENTS] = s[sg.DEFINITION][sd.SEGMENTS] - 1

    s[sg.CONTINUATIONS] = []


def attach_node(s):
    if sg.TREE_ROOT_NODE in s:
        parent_node = s[sg.TREE_ROOT_NODE]
    else:
        parent_node = s[sg.PARENT_SEGMENT][sg.NODE]
    length_node = parent_node.attach_new_node('tree_segment_length')
    node = length_node.attach_new_node('tree_segment_rotation')
    s[sg.LENGTH_NODE] = length_node
    s[sg.NODE] = node


def length(s):
    age = s[sg.TREE_ROOT][sg.AGE]
    length_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.LENGTH]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    node = s[sg.LENGTH_NODE]
    rng = s[sg.RNG]
    node.set_z(length_func(age, rng) / segments)


def continuations(s):
    if s[sg.REST_SEGMENTS] > 0: # Not the last segment?
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


def radius(s):
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    radius_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.RADIUS]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]

    if sg.TREE_ROOT_NODE in s:  # Trunk of the tree
        s[sg.ROOT_RADIUS] = radius_func(age, 0, rng)

    s[sg.RADIUS] = radius_func(age, ratio, rng)


def bending(s):
    age = s[sg.TREE_ROOT][sg.AGE]
    segments = s[sg.STEM_ROOT][sg.DEFINITION][sd.SEGMENTS]
    rest_segments = s[sg.REST_SEGMENTS]
    bending_func = s[sg.STEM_ROOT][sg.DEFINITION][sd.BENDING]
    ratio = (segments - rest_segments) / segments
    rng = s[sg.RNG]

    pitch, roll = bending_func(age, ratio, rng)

    s[sg.NODE].set_hpr(0, pitch / segments, roll / segments)

# def basic_curvature(s):
#     # FIXME: There's an underdocumented helical curvature, too.
#     if s[sg.DEFINITION][sd.CURVATURE] == sc.SINGLE:
#         curve = s[sg.DEFINITION][sd.CURVE] / s[sg.DEFINITION][sd.SEGMENTS]
#     elif s[sg.DEFINITION][sd.CURVATURE] == sc.DOUBLE:
#         if s[sg.REST_SEGMENTS] > s[sg.DEFINITION][sd.SEGMENTS] / 2.0:
#             curve = s[sg.DEFINITION][sd.CURVE] / (s[sg.DEFINITION][sd.SEGMENTS] / 2.0)
#         else:
#             curve = -s[sg.DEFINITION][sd.CURVEBACK] / (s[sg.DEFINITION][sd.SEGMENTS] / 2.0)
#     else:
#         raise Exception
#     curve += (s[sg.RNG].random() * 2.0 - 1.0) * s[sg.DEFINITION][sd.CURVE_VAR] / s[sg.DEFINITION][sd.SEGMENTS]
# 
#     # Compensating split debt
#     compensation = s[sg.CLONE_BENDING_DEBT] / s[sg.REST_SEGMENTS]
#     curve -= compensation
#     s[sg.CLONE_BENDING_DEBT] -= compensation
# 
#     # ...and apply.
#     s[sg.NODE].set_p(curve)
# 
# 
# def clone_curvature(s):
#     if sg.IS_NEW_CLONE in s:  # It's value is always `True`
#         local_tree_up = s[sg.NODE].get_relative_vector(
#             s[sg.TREE_ROOT_NODE],
#             up,
#         )
#         declination = local_tree_up.angle_deg(up)
#         split_angle = s[sg.DEFINITION][sd.SPLIT] + s[sg.RNG].uniform(-1, 1) * s[sg.DEFINITION][sd.SPLIT_VAR] - declination
#         split_angle = max(0, split_angle)
#         s[sg.NODE].set_p(s[sg.NODE], split_angle)
#         s[sg.CLONE_BENDING_DEBT] += split_angle
# 
#         # Split rotation around tree's z
#         angle_magnitude = 20.0 + 0.75 * (30.0 + abs(declination - 90.0)) * s[sg.RNG].random() ** 2
#         split_rotation = angle_magnitude * s[sg.RNG].choice([-1, 1]) * s[sg.DEFINITION][sd.SPLIT_ROTATION]
#         s[sg.NODE].set_hpr(
#             s[sg.NODE],
#             s[sg.NODE].get_relative_vector(
#                 s[sg.TREE_ROOT_NODE],
#                 Vec3(split_rotation, 0, 0),
#             ),
#         )
# 
# 
# def create_continuations(s):
#     if s[sg.REST_SEGMENTS] == s[sg.DEFINITION][sd.SEGMENTS]:  # First segment
#         clones = s[sg.DEFINITION][sd.BASE_CLONES]
#     else:  # Later segment
#         clones = s[sg.DEFINITION][sd.CLONES]
# 
#     error = s[sg.STEM_ROOT][sg.SPLITTING_ACC]
#     clones_smoothed = clones + error
#     
#     bonus_split_chance = clones_smoothed % 1
#     if s[sg.RNG].random() <= bonus_split_chance:
#         clones_integered = math.ceil(clones_smoothed)
#     else:
#         clones_integered = max(0, math.floor(clones_smoothed))
# 
#     error_correction = clones_integered - clones
#     s[sg.STEM_ROOT][sg.SPLITTING_ACC] -= error_correction
# 
#     # Create the next segment
#     if s[sg.REST_SEGMENTS] > 0: # Not the last segment?
#         # Regular continuations
#         s[sg.CONTINUATIONS].append(
#             {
#                 sg.DEFINITION: s[sg.DEFINITION],
#                 sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
#                 sg.TREE_ROOT_NODE: s[sg.TREE_ROOT_NODE],
#                 sg.STEM_ROOT: s[sg.STEM_ROOT],
#                 sg.PARENT_SEGMENT: s,
#                 sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
#                 sg.CLONE_BENDING_DEBT: s[sg.CLONE_BENDING_DEBT],
#             },
#         )
#         # Clones
#         for idx in range(clones_integered):
#             s[sg.CONTINUATIONS].append(
#                 {
#                     sg.DEFINITION: s[sg.DEFINITION],
#                     sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
#                     sg.TREE_ROOT_NODE: s[sg.TREE_ROOT_NODE],
#                     sg.STEM_ROOT: s[sg.STEM_ROOT],
#                     sg.PARENT_SEGMENT: s,
#                     sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
#                     sg.IS_NEW_CLONE: True,
#                     sg.CLONE_BENDING_DEBT: s[sg.CLONE_BENDING_DEBT],
#                 },
#             )


def expand(s):
    set_up_rng(s)
    hierarchy(s)
    attach_node(s)
    length(s)
    radius(s)
    bending(s)
    if s[sg.REST_SEGMENTS] > 0:
        continuations(s)


def expand_fully(s):
    sheets = [s]
    while sheets:
        sheet = sheets.pop()
        expand(sheet)
        sheets += sheet[sg.CONTINUATIONS]


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