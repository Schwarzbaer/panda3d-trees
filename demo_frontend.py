import sys
import random

from panda3d.core import NodePath
from panda3d.core import KeyboardButton

from direct.showbase.ShowBase import ShowBase

from tree_specs import QuakingAspen, BlackTupelo, WeepingWillow, CaliforniaBlackOak, BoringTree
from style_def import Skeleton, SkeletonAndRing, Bark
from tree_generation import StemSegment
import geometry


def replace_tree(tree_def=BoringTree, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root
    tree_root.remove_node()
    tree_root = NodePath('autotree')
    tree_root.reparent_to(base.render)

    rng = random.Random(seed)

    # style = Skeleton
    # style = Bark
    style = SkeletonAndRing

    tree = StemSegment(tree_def, tree_root, rng_seed=rng)
    tree.expand()
    geometry.line_art(tree, style)
    geometry.trimesh(tree).reparent_to(tree_root)


def move_camera(task):
    rot_speed = 360 / 3
    dt = globalClock.dt
    turn = 0
    pitch = 0
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('a')):
        turn += rot_speed * dt
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('d')):
        turn -= rot_speed * dt
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('s')):
        pitch += rot_speed * dt
    if base.mouseWatcherNode.is_button_down(KeyboardButton.ascii_key('w')):
        pitch -= rot_speed * dt
    base.camera.set_h(base.camera.get_h() + turn)
    old_pitch = base.camera.get_p()
    new_pitch = max(min(old_pitch + pitch, 89.9), -89.9)
    base.camera.set_p(new_pitch)
    return task.cont


# Actual application

ShowBase()
base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, 0, 1.6)
base.cam.set_y(-10)
base.add_task(move_camera)


global tree_root
tree_root = NodePath('autotree')


base.accept('1', replace_tree, extraArgs=[BoringTree])
base.accept('2', replace_tree, extraArgs=[QuakingAspen])
base.accept('3', replace_tree, extraArgs=[BlackTupelo])
base.accept('4', replace_tree, extraArgs=[WeepingWillow])
base.accept('5', replace_tree, extraArgs=[CaliforniaBlackOak])
base.accept('shift-1', replace_tree, extraArgs=[BoringTree, 0])
base.accept('shift-2', replace_tree, extraArgs=[QuakingAspen, 0])
base.accept('shift-3', replace_tree, extraArgs=[BlackTupelo, 0])
base.accept('shift-4', replace_tree, extraArgs=[WeepingWillow, 0])
base.accept('shift-5', replace_tree, extraArgs=[CaliforniaBlackOak, 0])


replace_tree(tree_def=BoringTree, seed=0)
base.run()
