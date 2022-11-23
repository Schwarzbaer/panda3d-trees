# TODO
# * bend = 180.0, bend_back = 1.0  # Values are used wrong way around?
# * Corrent number of branches


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




# Input

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

    treeify(tree_root, tree_def, rng, style)
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
base.camera.set_pos(0, -150, 1.6)
base.camera.look_at(0, 0, 10)


global tree_root
tree_root = NodePath('autotree')


base.accept('1', replace_tree, extraArgs=[QuakingAspen])
base.accept('2', replace_tree, extraArgs=[BlackTupelo])
base.accept('3', replace_tree, extraArgs=[WeepingWillow])
base.accept('4', replace_tree, extraArgs=[CaliforniaBlackOak])
base.accept('0', replace_tree, extraArgs=[BoringTree])


base.add_task(rotate_tree)
replace_tree(tree_def=BoringTree)
base.run()
