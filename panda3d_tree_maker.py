import sys
import random
import math

from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import LineSegs
from panda3d.core import KeyboardButton

from direct.showbase.ShowBase import ShowBase


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
# nSegSplits -> branches
# nBaseSplits -> trunk_splits
# nSplitAngle -> split_angle
# nSplitAngleV -> split_angle_var
#
# missing: error diffusion, clone rotation, split angle diffusion, ...
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




class BoringTree:
    segments        = 10.0
    length          = 20.0
    length_var      =  0.0
    trunk_splits    = False
    branches        =  0.0
    split_angle     =  0.0
    split_angle_var =  0.0
    diameter        =  1.0
    diameter_var    =  0.0
    bend            =  0.0
    bend_back       = False
    bend_var        =  0.0
    twist           =  0.0
    twist_var       =  0.0


class SampleTree: # Weeping Willow
    segments        =   8.0
    length          =  17.2
    length_var      =   2.5
    trunk_splits    =   2.0
    branches        =   0.1
    split_angle     =   3.0
    split_angle_var =   0.0
    diameter        =   1.0
    diameter_var    =   0.0
    bend            =   0.0
    bend_back       = False
    bend_var        = 120.0
    twist           =   0.0
    twist_var       =   0.0


def stemletify(sheet):
    sd = sheet['stem_definition']
    child_sheets = []

    slrng_seed = random.Random(sheet['rng']).random()
    slrng = random.Random(slrng_seed)  # stemlet rng

    # The branches first segment has no clones. The second might be a
    # splitting trunk, or a regularly cloning segment as all those to
    # come.
    if (sd.segments == sheet['rest_segments']):
        branches_base = 0
    elif (sd.segments - 1 == sheet['rest_segments']) and sd.trunk_splits:
        branches_base = sd.trunk_splits
    else:
        branches_base = sd.branches

    # Floyd-Steinberg-ishly diffused branching determination
    branching_acc = sheet['branching_acc']
    if slrng.random() <= (branches_base - math.floor(branches_base)) + branching_acc:
        branches = math.floor(branches_base) + 1
    else:
        branches = math.floor(branches_base)
    branching_acc -= branches - branches_base

    for branch_idx in range(branches + 1):
        # rngs
        gdrng_seed = slrng.random()
        gdrgn = random.Random(gdrng_seed)  # geometry data rng
        
        # stemlet data
        stemlet_length = sd.length / sd.segments + gdrgn.uniform(-1, 1) * sd.length_var / sd.segments
        # Basic bend
        if not sd.bend_back:
            stemlet_bend = sd.bend / sd.segments + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
        else:
            is_lower_half = sheet['rest_segments'] <= sd.segments / 2
            if is_lower_half:
                stemlet_bend = sd.bend / (sd.segments / 2) + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
            else:
                stemlet_bend = -sd.bend_back / (sd.segments / 2) + gdrgn.uniform(-1, 1) * sd.bend_var / sd.segments
        # Split angle for branching
        if branch_idx > 0:
            local_tree_up = sheet['root_node'].get_relative_vector(sheet['tree_root_node'], Vec3(0, 0, 1))
            declination = math.acos(local_tree_up.z) / math.pi * 360.0
            split_angle = max(sd.split_angle + gdrgn.uniform(-1, 1) * sd.split_angle_var - declination, 0)
            stemlet_bend += split_angle
        # Split rotation around tree's z
        if branch_idx > 0 and branch_idx > 0: # FIXME: ...in contradiction to the paper
            local_tree_up = sheet['root_node'].get_relative_vector(sheet['tree_root_node'], Vec3(0, 0, 1))
            declination = math.acos(local_tree_up.z) / math.pi * 360.0
            angle_magnitude = 20 + 0.75 * (30 + abs(declination - 90)) * gdrgn.random() ** 2
            stemlet_z_rotation = angle_magnitude * random.choice([-1, 1])
        else:
            stemlet_z_rotation = 0
        # Others
        stemlet_twist    = sd.twist / sd.segments + gdrgn.uniform(-1, 1) * sd.twist_var  / sd.segments
        stemlet_diameter = sd.diameter             + gdrgn.uniform(-1, 1) * sd.diameter_var

        # stemlet node
        node = sheet['root_node'].attach_new_node('stemlet')
        node.set_z(sheet['root_length'])
        node.set_h(stemlet_twist)
        node.set_p(stemlet_bend)
        node.set_hpr(node, node.get_relative_vector(sheet['tree_root_node'], Vec3(0, 0, stemlet_z_rotation)))
        
        # stemlet model
        
        # stemlet_model = base.loader.load_model('models/smiley')
        # stemlet_model.reparent_to(node)
        # 
        # stemlet_model.set_pos(0, 0, stemlet_length / 2.0)
        # stemlet_model.set_sz(stemlet_length * 0.5)
        # stemlet_model.set_sx(stemlet_diameter * 0.5)
        # stemlet_model.set_sy(stemlet_diameter * 0.5)

        segs = LineSegs()
        segs.set_thickness(2.0)
        segs.set_color(1, 1, 1,1)
        segs.move_to(0, 0, 0)
        segs.draw_to(0, 0, stemlet_length)
        node.attach_new_node(segs.create())

        # Child segments
        if sheet['rest_segments'] > 1:
            child_sheet = dict(
                tree_root_node  = sheet['tree_root_node'],
                root_node       = node,
                rest_segments   = sheet['rest_segments'] - 1,
                root_length     = stemlet_length,
                stem_definition = sd,
                rng             = gdrng_seed,
                branching_acc   = branching_acc,
            )
            child_sheets.append(child_sheet)

    return child_sheets


def treeify(root, sd, rng):
    """
    Attach a (botanical) tree's geometry to a NodePath.

    root
        NodePath to add tree to
    sd
        Stem definition
    rng
        :class:`random.Random` instance to use
    """
    stemlet_sheet = dict(
        tree_root_node  = root,
        root_node       = root,
        rest_segments   = sd.segments,
        root_length     = 0.0,
        stem_definition = sd,
        rng             = rng,
        branching_acc   = 0.0,  # Accumulator for Floyd-Steinberg-ish error diffusion
    )
    sheets = [stemlet_sheet]

    while sheets:
        sheet = sheets[0]
        sheets = sheets[1:]
        children = stemletify(sheet)
        sheets += children


# Input

def replace_tree(tree_def, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root
    tree_root.remove_node()
    tree_root = NodePath('autotree')
    tree_root.reparent_to(base.render)

    rng = random.Random(seed)
    treeify(tree_root, tree_def, rng)

base.accept('1', replace_tree, extraArgs=[SampleTree])
base.accept('2', replace_tree, extraArgs=[BoringTree])


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

replace_tree(SampleTree, 0)
base.run()
