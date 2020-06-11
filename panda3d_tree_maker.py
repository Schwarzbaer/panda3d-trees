import sys
import random
import math

from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import KeyboardButton

from direct.showbase.ShowBase import ShowBase

from tree_specs import QuakingAspen, BlackTupelo, WeepingWillow, CaliforniaBlackOak, BoringTree
from tree_specs import SplitRotation

import geometry


ShowBase()
base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, -50, 1.6)
base.camera.look_at(0, 0, 10)


global tree_root
tree_root = NodePath('autotree')

# 4.1 The curved stem
# nCurveRes -> segments
# nCurve -> bend
# nCurveBack -> bend_back
# Instead of using a variance of 0 to max, we use -max to max:
#   bend = nCurve + nCurveV
#   bend_var = nCurveV / 2
# missing: helical stem
#
# The stem is divided into nCurveRes segments.
# if nCurveV < 0.0:
#     stem is formed as a helix. The declination angle is specified by magnitude(nCurveVary)
#     FIXME: That bit is unclear; Are we talking about the twist value?
# elif not nCurveBack:
#     the z-axis of each segment on the stem is rotated away from z-axis of the previous segment by (nCurve/nCurveRes) degrees
# else:
#     in the first half of the stemis rotated (nCurve/(nCurveRes/2)) degrees and
#     each in the second half is rotated (nCurveBack/(nCurveRes/2)) degrees.
# In either case, a random rotation of magnitude (nCurveV/nCurveRes) is also added for each segment.


# 4.2 Stem Splits
# nSegSplits -> splits
# nBaseSplits -> trunk_splits
# nSplitAngle -> split_angle
# nSplitAngleV -> split_angle_var
#
# * Fractional branching: DONE
#   At each segment, a stems can split into multiple clones. The frequency of splitting is defined by nSegSplits.
#   This is the number of new clones added for each segment along the stem and is usually between 0 and 1, with 1 referring to a dichotomous split
#   on every  segment. A value of 2 would indicate a ternary split.
#   There is an additional parameter nBaseSplits that specifies the equivalent of nSegSplits at the end of the first segment of the trunk.
#   This allows for an independent number of splits at the base of the tree, thus permitting trees that seem to have multiple trunks with few
#   further splitting tendencies.
#   Fractional values of nSegSplits will cause additional splits to be evenly distributed throughout all segments of all stems in that particular
#   level of recursion. For example, an nSegSplits of 1.2 will form one clone on 80% of the level n segments and two clones on 20% of the segments.
#   Note that this yields an average number of 1.2 splits per segment.  Using random numbers simplistically to distribute the fractional part of
#   nSegSplits is unacceptable because when, by chance, several consecutive segments all get the extra split, they can forman unnaturally large
#   number of stems in close proximity on part of the tree.
# * Error diffusion: DONE
#   To evenly distribute the splits, we use a technique similar to Floyd-Steinburg Error Diffusion.
#   For each recursive level, a global value holds an "error value" initialized to 0.0.
#   Each time nSegSplits is used, this error is added to create a SegSplits_effective which is rounded to the nearest integer.
#   The difference (SegSplits_effective - nSegSplits) is subtracted from the error.
#   So, if a value is rounded up, it is more likely that the next value will be rounded down (and vice versa).
# * Angle split? DONE
#   If there are any clones, then the z-axes of the stem and its clones each rotate away from the z-axis of the previous segment by
#       anglesplit = (nSplitAngle ± nSplitAngleV) - declination, limited to a minimum of 0
#     where the "declination" angle (defined here as the angle of a stem from the tree's positive z-axis) can be found by taking the inverse cosine
#     of the z component of a unit z vector passed through the current matrix transformation of the relative coordinate system.
#   The first clone continues the original mesh and cannot rotate around the z-axis or it would twist the mesh (i.e., if one rotated one of the
#     circular faces on a cylinder about the longitudinal axis, the resulting section of geometry would render as a hourglass shape).
#   This anglesplit is later distributed over the remaining segments in the reverse direction so that the stem will tend to return to its originally
#     intended direction. This compensation prevents overspreading due to large numbers of stem splits. The extent that any level of stems spreads
#     out can be easily controlled using the curve parameters.
# * Stem split rotation around tree's z: DONE, kinda. No information about rotation of any segments except the first of two are given.
#   A stem and its clones are also spread apart by rotating them about an axis that is parallel to the z-axis of the tree.
#   In the normal case of a single clone, the original stem (which is continued after its clone is created) is rotated about the parallel axis by
#   an angle of magnitude:
#   [ 20 + 0.75 * (30 + | declination-90 |  )  *  RANDOM(0  to  1) ^ 2]
#   The sign of this angle is random as well.


# 4.3 Stem children
#
# nBranches: maximum number of child sub-stems that a stem can create over all of its segments.
# The actual number of children from any stem might be less than this maximum.
#
# Any stem that has been cloned or is, itself, a clone reduces its propensity to form clones by half.
# The function ShapeRatio(shape, ratio):
#   Shape                    Result
#   0 (conical)              0.2 + 0.8 * ratio
#   1 (spherical)            0.2 + 0.8 * sin(pi * ratio)
#   2 (hemispherical)        0.2 + 0.8 * sin(0.5 * pi * ratio)
#   3 (cylindrical)          1.0
#   4 (tapered cylindrical)  0.5 + 0.5 * ratio
#   5 (flame)                ratio <= 0.7: ratio / 0.7
#                            else        : (1.0 - ratio) / 0.3
#   6 (inverse conical)      1.0 - 0.8 * ratio
#   7 (tend flame)           ratio <= 0.7: 0.5 + 0.5 * ratio / 0.7
#                            else        : 0.5 + 0.5 * (1.0 - ratio) / 0.3
#   8 (envelope)             use pruning envelope (see Section 4.6)
#
# 
#   length_child_max = nLength ± nLengthV  # The maximum relative length as a fraction of its parent's specific length
#   offset_child = the position in meters of the child along the parent's length (from the base).
#   # The number of successive child stems (really "grandchildren") is computed as
#   for the first level of branches:
#     stems = stems_max * (0.2 + 0.8 * (length_child / length_parent) / length_child_max)
#   further levels of branches
#     stems = stems_max * (1.0 - 0.5 * (offset_child / length_parent))
#   scale_tree = Scale ± ScaleV
#   length_base = fractional bare area at the base of the tree calculated as (BaseSize * scale_tree)
#   length_trunk = (0Length ± 0LengthV) * scale_tree
#   if first_level_of_branches:
#     length_child = length_trunk * length_child_max * ShapeRatio((Shape, (length_trunk-offset_child)/(length_trunk - length_base))
#   else:
#     length_child = length_child_max * ( length_parent - 0.6 * offset_child)
#   # the z-axis of a child rotates away from the z-axis of its parent about the x-axis at an angle of:
#   if nDownAngleV >= 0.0:
#     downangle_child = nDownAngle ± nDownAngleV
#   else:
#     downangle_child = nDownAngle ± abs(nDownAngleV * (1 - 2 * conical((length_parent - offset_child) / (length_parent - length_base))))
#
# This can be used to linearly change the down angle based on the position of the child along its parent, as with the Black Tupelo's main branches
# seen in Plate 2b. Note how they are angled upward near the crown of the treeand angled downward near the bottom.


class StemletSheet:
    def __init__(self, tree_root_node, root_node=None, rest_segments=None, root_length=0.0, stem_definition=BoringTree, rng=0, splitting_acc=0.0,
                 split_rotate_acc=0.0):
        """
        tree_root_node
            NodePath of the root of the whole tree
        root_node
            The previous segment's NodePath. Defaults to tree_root_node
        rest_segments
            Number of segments left to create in this stem. Defaults to the number of segments in stem_definition.
        root_length
            The previous segment's length. Defaults to 0.0
        stem_definition
            The tree class. Defaults to :class:`BoringTree`
        rng
            Random seed to use for the next segment. Defaults to 0
        splitting_acc
            Accumulated error for Floyd-Steinberg-ish error diffusion of stem split angles. Defaults to 0.0
        split_rotate_acc
            Accumulated rotation of stem child segments
        """
        if rest_segments is None:
            rest_segments = stem_definition.segments
        if root_node is None:
            root_node = tree_root_node

        self.tree_root_node = tree_root_node
        self.root_node = root_node
        self.rest_segments = rest_segments
        self.root_length = root_length
        self.stem_definition = stem_definition
        self.rng = rng
        self.splitting_acc = splitting_acc
        self.split_rotate_acc = split_rotate_acc


def stemletify(sheet):
    """
    Takes a stemlet sheet, attaches relevant scene subgraphs to the 
    sheet's node, and returns a list of sheets for the next segments
    in this S-stem (continuation and possible split clones), and
    branches.
    """
    sd = sheet.stem_definition
    child_sheets = []  # dictionaries for StemletSheet kwargs. Can't finalize them
                       # until the rotation of all children has been accumulated.

    slrng_seed = random.Random(sheet.rng).random()
    slrng = random.Random(slrng_seed)  # stemlet rng

    # The stem's first segment has no clones. The second might be a
    # splitting trunk, or a regularly cloning segment as all those to
    # come.
    if (sd.segments == sheet.rest_segments):
        splits_base = 0
    elif (sd.segments - 1 == sheet.rest_segments) and sd.trunk_splits:
        splits_base = sd.trunk_splits
    else:
        splits_base = sd.splits

    # Floyd-Steinberg-ishly diffused splitting determination
    splitting_acc = sheet.splitting_acc
    if slrng.random() <= (splits_base - math.floor(splits_base)) + splitting_acc:
        splits = math.floor(splits_base) + 1
    else:
        splits = math.floor(splits_base)
    splitting_acc -= splits - splits_base

    # Create stem segments
    for split_idx in range(splits + 1):
        # rngs
        gdrng_seed = slrng.random()
        gdrgn = random.Random(gdrng_seed)  # geometry data rng
        
        # Segment length: segment_length
        stemlet_length = sd.length / sd.segments + gdrgn.uniform(-1, 1) * sd.length_var / sd.segments

        # Basic bend: stemlet_bend
        if not sd.bend_back:
            stemlet_bend = sd.bend / sd.segments + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
        else:
            is_lower_half = sheet.rest_segments <= sd.segments / 2
            if is_lower_half:
                stemlet_bend = sd.bend / (sd.segments / 2) + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
            else:
                stemlet_bend = -sd.bend_back / (sd.segments / 2) + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
        # Split angle: stemlet_bend
        if split_idx > 0:
            up = Vec3(0, 0, 1)
            local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, up)
            declination = local_tree_up.angle_deg(up)
            stemlet_bend += max(sd.split_angle + gdrgn.uniform(-1, 1) * sd.split_angle_var - declination, 0)
        # Split children's rotation around the parent's Z: stemlet_split_rotation
        if split_idx == 0:
            stemlet_split_rotation = 0.0
        else:
            if sd.split_rotate_mode == SplitRotation.HELICAL:
                sheet.split_rotate_acc += sd.split_rotate + gdrgn.uniform(-1, 1) * sd.split_rotate_var
            elif sd.split_rotate_mode == SplitRotation.COPLANAR:
                sheet.split_rotate_acc += -sd.split_rotate + gdrgn.uniform(-1, 1) * sd.split_rotate_var + 180
            else:
                raise ValueError("Unknown split_rotate_mode {}".format(sd.split_rotate_mode))
            sheet.split_rotate_acc = sheet.split_rotate_acc % 360
            stemlet_split_rotation = sheet.split_rotate_acc
        # Split rotation around tree's z: stemlet_z_rotation
        if split_idx > 0: # FIXME: ...in contradiction to the paper
            local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, Vec3(0, 0, 1))
            declination = math.acos(local_tree_up.z) / math.pi * 360.0
            angle_magnitude = 20 + 0.75 * (30 + abs(declination - 90)) * gdrgn.random() ** 2
            stemlet_z_rotation = angle_magnitude * random.choice([-1, 1]) * sd.split_tree_z
        else:
            stemlet_z_rotation = 0.0
                
        # Others
        stemlet_diameter = sd.diameter + gdrgn.uniform(-1, 1) * sd.diameter_var

        # stemlet node
        node = sheet.root_node.attach_new_node('stemlet')
        # Position at the end of parent
        node.set_z(sheet.root_length)
        # Rotate splits around their parent
        node.set_h(stemlet_split_rotation)
        # Bend: basic bend + split_angle
        node.set_p(node, stemlet_bend)
        # Rotate splits around the tree's z
        node.set_hpr(
            node,
            node.get_relative_vector(
                sheet.tree_root_node,
                Vec3(stemlet_z_rotation, 0, 0),
            ),
        )
        
        # stemlet model
        node.attach_new_node(geometry.line_art(stemlet_length, stemlet_diameter, sheet.rest_segments))

        # Child segments
        if sheet.rest_segments > 1:
            child_sheet = dict(
                tree_root_node  =sheet.tree_root_node,
                root_node       =node,
                rest_segments   =sheet.rest_segments - 1,
                root_length     =stemlet_length,
                stem_definition =sd,
                rng             =gdrng_seed,
                splitting_acc   =splitting_acc,
            )
            if split_idx > 0:
                child_sheet.update(dict(split_rotate_acc=0.0))
            child_sheets.append(child_sheet)

    if child_sheets:
        child_sheets[0]['split_rotate_acc'] = sheet.split_rotate_acc        
    return [StemletSheet(**cs) for cs in child_sheets]


def treeify(root, sd, rng):
    """
    Attach a (botanical) tree's geometry to a NodePath.

    root
        NodePath to add tree to
    sd
        Stem definition
    rng
        :class:`random.Random` seed
    """
    stemlet_sheet = StemletSheet(
        tree_root_node=root,
        stem_definition=sd,
        rng=rng,
    )
    sheets = [stemlet_sheet]

    while sheets:
        sheets += stemletify(sheets.pop())


# Input

def replace_tree(tree_def=BoringTree, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root
    tree_root.remove_node()
    tree_root = NodePath('autotree')
    tree_root.reparent_to(base.render)

    rng = random.Random(seed)
    treeify(tree_root, tree_def, rng)


base.accept('1', replace_tree, extraArgs=[QuakingAspen])
base.accept('2', replace_tree, extraArgs=[BlackTupelo])
base.accept('3', replace_tree, extraArgs=[WeepingWillow])
base.accept('4', replace_tree, extraArgs=[CaliforniaBlackOak])
base.accept('0', replace_tree, extraArgs=[BoringTree])


def rotate_tree(task):
    global tree_root

    rot_speed = 360 / 3
    dt = globalClock.dt
    turn = 0
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('a')):
        turn += rot_speed * dt
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('d')):
        turn -= rot_speed * dt
    tree_root.set_h(tree_root, turn)
    return task.cont



base.add_task(rotate_tree)


# Setup

replace_tree(tree_def=WeepingWillow)
base.run()
