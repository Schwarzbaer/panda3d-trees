import sys
import random
import math

from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import KeyboardButton

from direct.showbase.ShowBase import ShowBase

from tree_specs import QuakingAspen, BlackTupelo, WeepingWillow, CaliforniaBlackOak, BoringTree
from tree_specs import SplitRotation, SegmentType
from style_def import Skeleton, Bark

import geometry


ShowBase()
base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, -50, 1.6)
base.camera.look_at(0, 0, 10)


global tree_root
tree_root = NodePath('autotree')

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
# seen in Plate 2b. Note how they are angled upward near the crown of the tree and angled downward near the bottom.

# To generate animation:
# * build a Character with the entire joint hierarchy
# * put a TransformBlendTable on your geometry to map vertices to joints
# * each animation would require an AnimBundle that replicates the
#   Character's joint hierarchy and specifies a transform for each joint
#   each frame of the animation


class StemletSheet:
    def __init__(self, tree_root_node, root_node=None, rest_segments=None, root_length=0.0, stem_definition=BoringTree, rng=0, splitting_acc=0.0,
                 split_rotate_acc=0.0, bend_debt=0.0, style=Skeleton):
        """
        tree_root_node
            NodePath of the root of the whole tree
        root_node
            The previous segment's NodePath. Defaults to tree_root_node
        rest_segments
            Number of segments left to create in this stem. Defaults to
            the number of segments in stem_definition.
        root_length
            The previous segment's length. Defaults to 0.0
        stem_definition
            The tree class. Defaults to :class:`BoringTree`
        rng
            Random seed to use for the next segment. Defaults to 0
        splitting_acc
            Accumulated error for Floyd-Steinberg-ish error diffusion of
            stem split angles. Defaults to 0.0
        split_rotate_acc
            Accumulated rotation of stem child segments
        bend_debt
            bending accumulated through splits, the inverse of which is
            distributed over the rest of the stem, bending it back
            towards the original stem's direction.
        style
            Style specification with parameters for geometry generation.
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
        self.bend_debt = bend_debt
        self.style = style


def stemletify(sheet):
    segment_type = sheet.stem_definition.segment_type
    if segment_type == SegmentType.STEM:
        return stemify(sheet)
    elif segment_type == SegmentType.LEAF:
        model = loader.load_model("models/smiley")
        model.reparent_to(sheet.root_node)
        model.set_scale(0.5)
        return []
    else:
        raise ValueError("Unknown segment_type {}".format(segment_type))


def stemify(sheet):
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
        gdrng = random.Random(gdrng_seed)  # geometry data rng
        
        # Create stemlet node,and position at the end of the parent
        node = sheet.root_node.attach_new_node('stemlet')
        node.set_z(sheet.root_length)

        # Segment length: segment_length
        stemlet_length = sd.length / sd.segments + gdrng.uniform(-1, 1) * sd.length_var / sd.segments

        # Basic bend and split angle back bend: stemlet_bend, stemlet_debt_repayed
        if not sd.bend_back:
            stemlet_bend = sd.bend / sd.segments + gdrng.uniform(-1, 1) * sd.bend_var / sd.segments
        else:
            is_lower_half = sheet.rest_segments <= sd.segments / 2
            if is_lower_half:
                stemlet_bend = sd.bend / (sd.segments / 2) + gdrng.uniform(-1, 1) * sd.bend_var / sd.segments
            else:
                stemlet_bend = -sd.bend_back / (sd.segments / 2) + gdrng.uniform(-1, 1) * sd.bend_var / sd.segments
        stemlet_debt_repayed = sheet.bend_debt / sheet.rest_segments
        stemlet_bend -= stemlet_debt_repayed

        # Split angle: stemlet_bend
        if split_idx > 0:
            up = Vec3(0, 0, 1)
            local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, up)
            declination = local_tree_up.angle_deg(up)
            split_angle = max(sd.split_angle + gdrng.uniform(-1, 1) * sd.split_angle_var - declination, 0)
            stemlet_bend += split_angle
        else:
            split_angle = 0.0

        # Bend: basic bend + split_angle
        node.set_p(node, stemlet_bend)

        # Split children's rotation around the parent's Z: stemlet_split_rotation
        if split_idx == 0:
            stemlet_split_rotation = 0.0
        else:
            if sd.split_rotate_mode == SplitRotation.HELICAL:
                sheet.split_rotate_acc += sd.split_rotate + gdrng.uniform(-1, 1) * sd.split_rotate_var
            elif sd.split_rotate_mode == SplitRotation.COPLANAR:
                sheet.split_rotate_acc += -sd.split_rotate + gdrng.uniform(-1, 1) * sd.split_rotate_var + 180
            else:
                raise ValueError("Unknown split_rotate_mode {}".format(sd.split_rotate_mode))
            sheet.split_rotate_acc = sheet.split_rotate_acc % 360
            stemlet_split_rotation = sheet.split_rotate_acc

        # Apply node to split rotation
        node.set_h(stemlet_split_rotation)

        # Split rotation around tree's z: stemlet_z_rotation
        if split_idx > 0: # FIXME: ...in contradiction to the paper
            local_tree_up = sheet.root_node.get_relative_vector(sheet.tree_root_node, Vec3(0, 0, 1))
            declination = math.acos(local_tree_up.z) / math.pi * 360.0
            angle_magnitude = 20 + 0.75 * (30 + abs(declination - 90)) * gdrng.random() ** 2
            stemlet_z_rotation = angle_magnitude * gdrng.choice([-1, 1]) * sd.split_tree_z
        else:
            stemlet_z_rotation = 0.0
                
        # Apply split rotation around the tree's z
        node.set_hpr(
            node,
            node.get_relative_vector(
                sheet.tree_root_node,
                Vec3(stemlet_z_rotation, 0, 0),
            ),
        )

        # Stem diameter
        if sd.segment_type == SegmentType.STEM:
            # Basic taper
            base_diameter = sd.diameter + gdrng.uniform(-1, 1) * sd.diameter_var
            runlength = 1 - (sheet.rest_segments + 1) / (sd.segments + 1)  # Z
            if sd.taper <= 1:
                unit_taper = sd.taper
            elif 1 < sd.taper <= 2:
                unit_taper = 2 - sd.taper
            else:
                unit_taper = 0
            taper_z = base_diameter * (1 - unit_taper * runlength)  # taper_z_top = 1 - (sheet.rest_segments) / (sd.segments + 1)
            if sd.taper < 1:
                stemlet_diameter = taper_z
            else:
                Z_2 = (1 - runlength) * sd.length
                if sd.taper < 2 or Z_2 < taper_z:
                    depth = 1
                else:
                    depth = sd.taper - 2
                if sd.taper < 2:
                    Z_3 = Z_2
                else:
                    Z_3 = abs(Z_2 - 2 * taper_z * int(Z_2 / (2 * taper_z) + 0.5))
                if sd.taper < 2 and Z_3 >= taper_z:
                    stemlet_diameter = taper_z
                else:
                    stemlet_diameter = (1 - depth) * taper_z + depth * math.sqrt(taper_z ** 2 - (Z_3 - taper_z) ** 2)
            # Flare
            stemlet_diameter *= sd.flare * (100 ** (1 - 8 * runlength) - 1) / 100 + 1
        
        # stemlet model
        node.attach_new_node(
            geometry.line_art(
                sd,
                stemlet_length,
                stemlet_diameter,
                sheet.rest_segments,
                sheet.style,
            ),
        )

        # Stem-continuing segments
        if sheet.rest_segments > 1:
            if split_idx == 0:
                split_rotate_acc = None
            else:
                split_rotate_acc = 0.0
            child_sheet = StemletSheet(
                tree_root_node  =sheet.tree_root_node,
                root_node       =node,
                rest_segments   =sheet.rest_segments - 1,
                root_length     =stemlet_length,
                stem_definition =sd,
                rng             =gdrng_seed,
                splitting_acc   =splitting_acc,
                bend_debt       =sheet.bend_debt - stemlet_debt_repayed + split_angle,
                split_rotate_acc=split_rotate_acc,
                style           =sheet.style,
            )
            child_sheets.append(child_sheet)

        # Child stemlets
        if sd.child_definition is not None:
            child_node = node.attach_new_node('child')
            child_node.set_pos(0, 0, stemlet_length)
            child_node.set_p(45)
            child_sheet = StemletSheet(
                tree_root_node  =sheet.tree_root_node,
                root_node       =child_node,
                stem_definition =sd.child_definition,
                rng             =gdrng_seed,
                style           =sheet.style,
            )
            child_sheets.append(child_sheet)

    for child in child_sheets:
        if child.split_rotate_acc is None:
            child.split_rotate_acc = sheet.split_rotate_acc        

    return child_sheets


def treeify(root, sd, rng, style=Skeleton):
    """
    Attach a (botanical) tree's geometry to a NodePath.

    root
        NodePath to add tree to
    sd
        Stem definition
    rng
        :class:`random.Random` seed

    style
        Style definition to use for geometry
    """
    stemlet_sheet = StemletSheet(
        tree_root_node=root,
        stem_definition=sd,
        rng=rng,
        style=style,
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
    tree_root.set_h(-90)

    rng = random.Random(seed)

    style = Bark  # Skeleton

    treeify(tree_root, tree_def, rng, style)
    # tree_root.flatten_strong()
    print("--------------------------")
    tree_root.ls()


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
