import random
import math
import enum

from panda3d.core import Vec3
from panda3d.core import NodePath

from tree_specs import BoringTree, SegmentType, SplitRotation


# A tree's wooden parts are made of a hierarchy of stems.
# Stems are sequences of `sd.SEGMENT` segments.
# Each segment may have one or more `sg.CONTINUATIONS`, continuing
#   the current stem. A segment without continuations ends this run of
#   the stem.
# There are three basic modes of how a stem bends and twists:
#   * Basic: Each segment pitches up relative to its parent. The total
#     bent of the tree is `bend` degrees.
#   * S-shaped: In the first half of the stem, segments pitch up a total
#     of `bend` degrees, while in the second half they pitch down a
#     total of `bend_back` degrees.
#   * Helical: FIXME
#   To each bend, a random amount of a magnitude of `sd.CURVE_VAR` is
#   added.
# After each segment (that is not the last in the stem), 


class StemType(enum.Enum):
    STEM = 1
    LEAF = 2


class StemCurvature(enum.Enum):
    SINGLE = 1
    DOUBLE = 2
sc = StemCurvature


class StemDefinition(enum.Enum):
    SEGMENTS = 1   # Number of segments in the stem
    LENGTH = 2     # Length of the stem
    RADIUS = 3     # Radius of the stem (FIXME: ...at the base?)
    CURVATURE = 4  # 
    CURVE = 5      # Curvature of the whole stem in degrees (half the stem in Stemurvature.DOUBLE)
    CURVEBACK = 6  # Backwards curvature of the second half of the stem in DOUBLE mode.
    CURVE_VAR = 7  # Magnitude of random vvariane to the curve over the stem; Divide by number of segments for variance per segment.


class Segment(enum.Enum):
    RNG_SEED = 8        # Seed for the random number generator.
    RNG = 9             # The random nnumber generator itself.
    DEFINITION = 1      # The StemDefinition for this stem.
    TREE_ROOT_NODE = 2  # The NodePath representing the tree's starting point.
    STEM_ROOT = 3       # The first segment of the stem.
    PARENT_SEGMENT = 4  # The segment from which this one sprouts.
    NODE = 5            # The NodePath representing this segment.
    REST_SEGMENTS =  6  # The number of segments left in the stem, inluding this one.
    CONTINUATIONS = 7   # Segments that continue the stem.


sd = StemDefinition
BoringTree = {
    sd.SEGMENTS: 4,
    sd.LENGTH: 4.0,
    sd.RADIUS: 0.25,
    sd.CURVATURE: sc.DOUBLE,
    sd.CURVE: 30.0,
    sd.CURVEBACK: 60.0,
    sd.CURVE_VAR: 60.0,
}


sg = Segment


def expand(s):
    if sg.RNG_SEED not in s:
        s[sg.RNG_SEED] = 0
    if sg.RNG not in s:
        s[sg.RNG] = random.Random(s[sg.RNG_SEED])

    if sg.TREE_ROOT_NODE not in s:
        # This segment is the root of the tree
        s[sg.TREE_ROOT_NODE] = NodePath('tree_root')

    # Attach the segment's node and move it into place
    if sg.PARENT_SEGMENT not in s:
        # This segment is (still) the tree's root
        s[sg.NODE] = s[sg.TREE_ROOT_NODE].attach_new_node('tree_segment')
    else:
        s[sg.NODE] = s[sg.PARENT_SEGMENT][sg.NODE].attach_new_node('tree_segment')
    s[sg.NODE].set_z(s[sg.DEFINITION][sd.LENGTH] / s[sg.DEFINITION][sd.SEGMENTS])
        
    # If this is a new stem, set the rest segment number.
    if sg.STEM_ROOT not in s:
        s[sg.STEM_ROOT] = s
        s[sg.REST_SEGMENTS] = s[sg.DEFINITION][sd.SEGMENTS]

    # Basic curvature
    # FIXME: There's an underdocumented helical curvature, too.
    if s[sg.DEFINITION][sd.CURVATURE] == sc.SINGLE:
        curve = s[sg.DEFINITION][sd.CURVE] / s[sg.DEFINITION][sd.SEGMENTS]
    elif s[sg.DEFINITION][sd.CURVATURE] == sc.DOUBLE:
        if s[sg.REST_SEGMENTS] > s[sg.DEFINITION][sd.SEGMENTS] / 2.0:
            curve = s[sg.DEFINITION][sd.CURVE] / (s[sg.DEFINITION][sd.SEGMENTS] / 2.0)
        else:
            curve = -s[sg.DEFINITION][sd.CURVEBACK] / (s[sg.DEFINITION][sd.SEGMENTS] / 2.0)
    else:
        raise Exception
    curve += (s[sg.RNG].random() * 2.0 - 1.0) * s[sg.DEFINITION][sd.CURVE_VAR] / s[sg.DEFINITION][sd.SEGMENTS]
    s[sg.NODE].set_p(curve)

    # Create the next segment
    s[sg.CONTINUATIONS] = []
    if s[sg.REST_SEGMENTS] > 1:
        s[sg.CONTINUATIONS].append(
            {
                sg.DEFINITION: s[sg.DEFINITION],
                sg.RNG_SEED: s[sg.RNG].randint(0, 2<<16 - 1),
                sg.TREE_ROOT_NODE: s[sg.TREE_ROOT_NODE],
                sg.STEM_ROOT: s[sg.STEM_ROOT],
                sg.PARENT_SEGMENT: s,
                sg.REST_SEGMENTS: s[sg.REST_SEGMENTS] - 1,
            },
        )


def expand_fully(s):
    sheets = [s]
    while sheets:
        sheet = sheets.pop()
        expand(sheet)
        sheets += sheet[sg.CONTINUATIONS]






#class StemSegment:
#    def __init__(self, stem_definition, tree_root_node, segment_root=None,
#                 rest_segments=None,
#                 rng_seed=0):
#        """
#        """
#        if rest_segments is None:
#            rest_segments = stem_definition.segments
#        print(rest_segments)
#
#        self.stem_definition = stem_definition
#        self.tree_root_node = tree_root_node
#        self.segment_root = segment_root
#        self.rest_segments = rest_segments
#        self.rng_seed = rng_seed
#
#        # DEBUG
#        self.segment_length = 1.0
#        self.segment_diameter = 1.0
#
#        # Children
#        self.stem_continuations = []
#        self.branch_children = []
#
#    def expand(self):
#        self.figure_out_hierarchy_and_attach_node()
#
#        if self.rest_segments > 1:
#            continuation = StemSegment(
#                self.stem_definition,
#                self.tree_root_node,  # It's on the same tree
#                segment_root=self,  # This segment is the next one's root
#                rest_segments=self.rest_segments-1,
#                rng_seed=0, # FIXME
#            )
#            self.stem_continuations.append(continuation)
#        
#        for child in self.stem_continuations:
#            child.expand()
#        for child in self.branch_children:
#            child.expand()
#
#    def figure_out_hierarchy_and_attach_node(self):
#        if self.segment_root is None:
#            node = self.tree_root_node.attach_new_node('stem_segment')
#        else:
#            node = self.segment_root.node.attach_new_node('stem_segment')
#            node.set_z(self.segment_root.segment_length)
#        self.node = node
#        node.set_python_tag('tree_generator_data', self)
#
#    def calculate_splits(self):
#        sd = self.stem_definition
#        if (sd.segments == self.rest_segments):
#            # First segment in stem does not split.
#            splits_base = 0
#        elif (sd.segments - 1 == self.rest_segments) and sd.trunk_splits:
#            # Second segment in stem uses `trunk_splits`.
#            splits_base = bd.trunk_splits
#        else:
#            # Third and later segments use `splits`.
#            splits_base = bd.splits
#    
#        # Floyd-Steinberg-ishly diffused splitting determination
#        splitting_acc = self.splitting_acc
#        if slrng.random() <= splits_base - math.floor(splits_base) + splitting_acc:
#            splits = math.floor(splits_base) + 1
#        else:
#            splits = math.floor(splits_base)
#        splitting_acc -= splits - splits_base
#    
#        fecundity = self.fecundity / (splits + 1)




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
