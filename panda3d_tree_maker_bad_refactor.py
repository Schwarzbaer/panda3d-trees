# TODO
# * bend = 180.0, bend_back = 1.0  # Values are used wrong way around?
# * Corrent number of branches


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


UP = Vec3(0, 0, 1)


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

# Transformations applied to stem segments:
# * bend / bend_back
# * Split angles and split angle debt
# * Rotation around tree z 
# * Light attraction
# * (RotateV seems implied by diagram)

# Transformations applied to stem children:
# * nDownAngleV
# * nRotate



# To generate animation:
# * build a Character with the entire joint hierarchy
# * put a TransformBlendTable on your geometry to map vertices to joints
# * each animation would require an AnimBundle that replicates the
#   Character's joint hierarchy and specifies a transform for each joint
#   each frame of the animation

# Missing:
# * Helical stems when nCurveBack < 0


class LeafSheet:
    def __init__(self, tree_root_node, root_node):
        self.tree_root_node = tree_root_node
        self.root_node = root_node

    def expand(self):
        pass  # FIXME


class StemletSheet:
    def __init__(self, tree_root_node, root_node=None,
                 rest_segments=None, root_length=0.0,
                 branch_definition=BoringTree, rng=0, splitting_acc=0.0,
                 child_rotate_acc=0.0, bend_debt=0.0, style=Skeleton,
                 branching_weight=1.0, stem_length=None,
                 stem_diameter=None, fecundity=1.0,
    ):
        """
        tree_root_node
            NodePath of the root of the whole tree
        root_node
            The previous segment's NodePath. Defaults to tree_root_node
        rest_segments
            Number of segments left to create in this stem. Defaults to
            the number of segments in branch_definition.
        root_length
            The previous segment's length. Defaults to 0.0
        branch_definition
            The tree class. Defaults to :class:`BoringTree`
        rng
            Random seed to use for the next segment. Defaults to 0
        splitting_acc
            Accumulated error for Floyd-Steinberg-ish error diffusion of
            stem split angles. Defaults to 0.0
        child_rotate_acc
            Accumulated rotation of stem child segments
        bend_debt
            bending accumulated through splits, the inverse of which is
            distributed over the rest of the stem, bending it back
            towards the original stem's direction.
        branching_weight
            The sheet's weight in the random choice of the distribution
            of a branch level's children.
        stem_length
            Total length of the stem.
        stem_diameter
            Basic untapered diameter of the stem.
        fecundity
            Propensity to form branches. Each stem split divides the
            fecundity by the number of splits
        """
        if rest_segments is None:
            rest_segments = branch_definition.segments
        if root_node is None:
            root_node = tree_root_node

        # Related nodes and sheets
        self.tree_root_node = tree_root_node
        self.root_node = root_node
        self.continuations = []  # Sheets that continue this stem
        self.children = []  # Sheets for new, smaller stems

        # Global data
        self.style = style

        # Stem data
        self.branch_definition = branch_definition
        self.stem_length = stem_length
        self.stem_diameter = stem_diameter

        # Stemlet data
        self.rng = rng
        self.rest_segments = rest_segments
        self.root_length = root_length
        self.splitting_acc = splitting_acc
        self.child_rotate_acc = child_rotate_acc
        self.bend_debt = bend_debt
        self.branching_weight = branching_weight
        self.fecundity = fecundity

    def expand(self):
        """
        Takes a stemlet sheet, attaches relevant scene subgraphs to the 
        sheet's node, and returns a list of sheets for the next segments
        in this S-stem (continuation and possible split clones), and
        branches.
        """
        bd = self.branch_definition  # We'll need this a lot.
        slrng = random.Random(self.rng)  # stemlet rng
    
        # The stem's first segment has no clones. The second might be a
        # splitting trunk, or a regularly cloning segment as all those
        # to come.
        if (bd.segments == self.rest_segments):
            splits_base = 0
        elif (bd.segments - 1 == self.rest_segments) and bd.trunk_splits:
            splits_base = bd.trunk_splits
        else:
            splits_base = bd.splits
    
        # Floyd-Steinberg-ishly diffused splitting determination
        splitting_acc = self.splitting_acc
        if slrng.random() <= splits_base - math.floor(splits_base) + splitting_acc:
            splits = math.floor(splits_base) + 1
        else:
            splits = math.floor(splits_base)
        splitting_acc -= splits - splits_base
    
        fecundity = self.fecundity / (splits + 1)
    
        # Create stem segments
        for split_idx in range(splits + 1):
            # Create stemlet node
            gdrng = random.Random(slrng.random())  # geometry data rng
            node = self.root_node.attach_new_node('stemlet')
            node.set_z(self.root_length)  # position at end of parent
    
            # Segment length. If this is the tree's root, the trunk's
            # length has to be determined.
            if self.stem_length is None:
                self.stem_length = bd.length + gdrng.uniform(-1, 1) * bd.length_var
            stemlet_length = self.stem_length / bd.segments
    
            # Same goes for diameter.
            if self.stem_diameter is None:
                self.stem_diameter = bd.diameter + gdrng.uniform(-1, 1) * bd.diameter_var
    
            # Basic bend and split angle back bend: stemlet_bend, stemlet_debt_repayed
            if not bd.bend_back:
                stemlet_bend = bd.bend / bd.segments + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
            else:
                is_lower_half = self.rest_segments <= bd.segments / 2
                if is_lower_half:
                    stemlet_bend = bd.bend / (bd.segments / 2) + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
                else:
                    stemlet_bend = -bd.bend_back / (bd.segments / 2) + gdrng.uniform(-1, 1) * bd.bend_var / bd.segments
            stemlet_debt_repayed = self.bend_debt / self.rest_segments
            stemlet_bend -= stemlet_debt_repayed
            node.set_p(node, stemlet_bend)
    
            # Upward / Light attraction
            local_tree_up = self.root_node.get_relative_vector(self.tree_root_node, UP)
            upward_angle = 0.0 - math.asin(local_tree_up.y) / (2.0 * math.pi) * 360.0 
    
            # forward = Vec3(0, 1, 0)
            # local_tree_forward = sheet.root_node.get_relative_vector(sheet.tree_root_node, forward)
            # orientation = math.acos(local_tree_forward.z)
            attraction_up = upward_angle / self.rest_segments * bd.upward_attraction
            node.set_p(node, attraction_up)
            
            # Split angle
            if split_idx > 0:
                local_tree_up = self.root_node.get_relative_vector(self.tree_root_node, UP)
                declination = local_tree_up.angle_deg(UP)
                split_angle = max(bd.split_angle + gdrng.uniform(-1, 1) * bd.split_angle_var - declination, 0)
            else:
                split_angle = 0.0
            node.set_p(node, split_angle)
    
            # Split rotation around tree's z
            if split_idx > 0: # FIXME: ...in contradiction to the paper
                local_tree_up = self.root_node.get_relative_vector(self.tree_root_node, UP)
                declination = math.acos(local_tree_up.z) / math.pi * 360.0
                angle_magnitude = 20 + 0.75 * (30 + abs(declination - 90)) * gdrng.random() ** 2
                stemlet_z_rotation = angle_magnitude * gdrng.choice([-1, 1]) * bd.split_tree_z
            else:
                stemlet_z_rotation = 0.0
            node.set_hpr(
                node,
                node.get_relative_vector(
                    self.tree_root_node,
                    Vec3(stemlet_z_rotation, 0, 0),
                ),
            )
    
            ### Stem children
            # Children only occur above the stem's base
            offset = (bd.segments - (self.rest_segments - 1)) / bd.segments
            child_rotate_acc = self.child_rotate_acc
            if (bd.child_definition is not None) and (offset > bd.length_base):
                if bd.shape is not None:  # Branches on the trunk
                    stems = bd.child_branches / bd.segments * (0.2 + 0.8 * offset) * fecundity
                else:  # Branches on branches
                    stems = bd.child_branches / bd.segments * (1.0 - 0.5 * offset) * fecundity
                children = math.floor(stems)            
                if random.random() <= stems % 1:
                    children += 1
    
                # Child length is determined using the Shape function
                offset_without_base = min(1, (1 - offset) / (1 - bd.length_base))
                if bd.shape is not None:  # Trunk uses different function...
                    child_scale = bd.shape(offset_without_base)
                else:
                    child_scale = 1 - 0.6 * offset
                child_length = self.stem_length * child_scale * bd.child_scale
    
                # Child branch diameter
                child_diameter = self.stem_diameter * (child_length / self.stem_length) ** bd.child_diameter_power
    
                for child_idx in range(children):
                    child_node = node.attach_new_node('child')
    
                    # Place at segment's end
                    child_node.set_pos(0, 0, stemlet_length)
        
                    # Rotate around the parent's Z (nRotate +/- nRotateV)
                    if bd.child_rotate_mode == SplitRotation.HELICAL:
                        child_rotate_acc += bd.child_rotate + gdrng.uniform(-1, 1) * bd.child_rotate_var
                    elif bd.child_rotate_mode == SplitRotation.COPLANAR:
                        child_rotate_acc += -bd.child_rotate + gdrng.uniform(-1, 1) * bd.child_rotate_var + 180
                    else:
                        raise ValueError("Unknown child_rotate_mode {}".format(bd.child_rotate_mode))
                    child_rotate_acc = child_rotate_acc % 360
                    child_node.set_h(child_rotate_acc)
    
                    # nDownAngle
                    if bd.child_down >= 0:
                        down_angle = bd.child_down + gdrng.uniform(-1, 1) * bd.child_down_var
                    else:
                        raise Exception
                        # down_angle = bd.child_down +- abs(bd.child_down_var * (1 - 2 * conical(lengthparent - offsetchild) / (lengthparent - lengthbase)))
                    child_node.set_p(down_angle)
    
                    # Upward attraction (copypasted from above)
                    local_tree_up = node.get_relative_vector(self.tree_root_node, UP)
                    upward_angle = 0.0 - math.asin(local_tree_up.y) / (2.0 * math.pi) * 360.0 
                    attraction_up = upward_angle / bd.child_definition.segments * bd.upward_attraction
                    child_node.set_p(child_node, attraction_up)
    
                    # ...and create the child's sheet.
                    if bd.child_definition.segment_type == SegmentType.STEM:
                        child_sheet = StemletSheet(
                            tree_root_node   =self.tree_root_node,
                            root_node        =child_node,
                            branch_definition=bd.child_definition,
                            rng              =slrng.random(),
                            style            =self.style,
                            stem_length      =child_length,
                            stem_diameter    =child_diameter,
                            fecundity        =fecundity,
                        )
                    else:
                        child_sheet = LeafSheet(
                            tree_root_node   =self.tree_root_node,
                            root_node        =child_node,
                        )
                    self.children.append(child_sheet)
    
            ### Stem-continuing sheet
            if self.rest_segments > 1:
                child_sheet = StemletSheet(
                    tree_root_node   =self.tree_root_node,
                    root_node        =node,
                    rest_segments    =self.rest_segments - 1,
                    root_length      =stemlet_length,
                    branch_definition=bd,
                    rng              =slrng.random(),
                    splitting_acc    =splitting_acc,
                    bend_debt        =self.bend_debt - stemlet_debt_repayed + split_angle,
                    child_rotate_acc =child_rotate_acc,
                    style            =self.style,
                    stem_length      =self.stem_length,
                    stem_diameter    =self.stem_diameter,
                    branching_weight =self.branching_weight / (splits + 1),
                    fecundity        =fecundity,
                )
                self.continuations.append(child_sheet)
    
            ### Graphics-related stuff
    
            # Stem diameter
            if bd.segment_type == SegmentType.STEM:
                # Basic taper
                runlength = 1 - (self.rest_segments + 1) / (bd.segments + 1)  # Z
                if bd.taper <= 1:
                    unit_taper = bd.taper
                elif 1 < bd.taper <= 2:
                    unit_taper = 2 - bd.taper
                else:
                    unit_taper = 0
                taper_z = self.stem_diameter * (1 - unit_taper * runlength)  # taper_z_top = 1 - (sheet.rest_segments) / (bd.segments + 1)
                if bd.taper < 1:
                    stemlet_diameter = taper_z
                else:
                    Z_2 = (1 - runlength) * self.stem_length
                    if bd.taper < 2 or Z_2 < taper_z:
                        depth = 1
                    else:
                        depth = bd.taper - 2
                    if bd.taper < 2:
                        Z_3 = Z_2
                    else:
                        Z_3 = abs(Z_2 - 2 * taper_z * int(Z_2 / (2 * taper_z) + 0.5))
                    if bd.taper < 2 and Z_3 >= taper_z:
                        stemlet_diameter = taper_z
                    else:
                        stemlet_diameter = (1 - depth) * taper_z + depth * math.sqrt(taper_z ** 2 - (Z_3 - taper_z) ** 2)
                # Flare
                stemlet_diameter *= bd.flare * (100 ** (1 - 8 * runlength) - 1) / 100 + 1

        # All done! Now all that is left is to remember some values...
        self.node = node
        self.stemlet_length = stemlet_length
        self.stemlet_diameter = stemlet_diameter

        # ...and recurse!
        for sheet in self.continuations:
            sheet.expand()
        for sheet in self.children:
            sheet.expand()




## Old drawing code
#              node.attach_new_node(
#                 geometry.line_art(
#                     bd,
#                     stemlet_length,
#                     stemlet_diameter,
#                     sheet.rest_segments,
#                     sheet.style,
#                 ),
#             )
#     
#         return child_sheets


def treeify(root, bd, rng):
    """
    Attach a (botanical) tree's geometry to a NodePath.

    root
        NodePath to add tree to
    bd
        Stem definition
    rng
        :class:`random.Random` seed
    """
    root_sheet = StemletSheet(
        tree_root_node=root,
        branch_definition=bd,
        rng=random.random(),
    )
    root_sheet.expand()
    return root_sheet


# Actual application

def replace_tree(tree_def=BoringTree, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root
    tree_root.remove_node()
    tree_root = NodePath('autotree')
    tree_root.reparent_to(base.render)

    rng = random.Random(seed)

    style = Skeleton
    # style = Bark

    root_sheet = treeify(tree_root, tree_def, rng)
    geometry.skin(root_sheet, style)
    tree_root.flatten_strong()
    # print("--------------------------")
    # tree_root.ls()


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


ShowBase()
base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, -100, 1.6)
base.camera.look_at(0, 0, 10)


global tree_root
tree_root = NodePath('autotree')
base.add_task(rotate_tree)
replace_tree(tree_def=BoringTree)
base.accept('1', replace_tree, extraArgs=[QuakingAspen])
base.accept('2', replace_tree, extraArgs=[BlackTupelo])
base.accept('3', replace_tree, extraArgs=[WeepingWillow])
base.accept('4', replace_tree, extraArgs=[CaliforniaBlackOak])
base.accept('0', replace_tree, extraArgs=[BoringTree])


base.run()
