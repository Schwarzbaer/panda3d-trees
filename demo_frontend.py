import sys
import random

from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import KeyboardButton
from panda3d.core import PointLight
from panda3d.core import AmbientLight

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText

from tree_specs import Segment as sg
from tree_species import boringBoringish as BoringTree
from homebrew import expand_fully
import geometry


def replace_tree(tree_def=BoringTree, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root_1
    global tree_root_2
    global tree_age
    tree_root_1.remove_node()
    tree_root_2.remove_node()

    rng = random.Random(seed)

    tree_1 = {
        sg.DEFINITION: BoringTree,
        sg.RNG_SEED: seed,
        sg.AGE: tree_age,
        sg.HELIOTROPIC_DIRECTION: Vec3(0, 0, 1),
    }
    expand_fully(tree_1, tropisms=False)
    tree_geom_node_1 = geometry.trimesh(tree_1)

    tree_2 = {
        sg.DEFINITION: BoringTree,
        sg.RNG_SEED: seed,
        sg.AGE: tree_age,
        sg.HELIOTROPIC_DIRECTION: Vec3(0, 0, 1),
    }
    expand_fully(tree_2, tropisms=True)
    tree_geom_node_2 = geometry.trimesh(tree_2)

    tree_root_1 = render.attach_new_node(tree_geom_node_1)
    tree_root_1.set_x(-4)
    tree_root_2 = render.attach_new_node(tree_geom_node_2)
    tree_root_2.set_x(4)
    #tree[sg.TREE_ROOT_NODE].reparent_to(tree_root)
    #import pdb; pdb.set_trace()


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

    global tree_root_1
    global tree_root_2
    for node in [tree_root_1, tree_root_2]:
        node.set_h(node.get_h() + turn)
        old_pitch = node.get_p()
        new_pitch = max(min(old_pitch + pitch, 89.9), -89.9)
        node.set_p(new_pitch)

    return task.cont


def change_tree_age(delta):
    global tree_age
    tree_age += delta
    text_age['text'] = str(tree_age)


# Actual application

ShowBase()


global tree_root_1
global tree_root_2
global tree_age
global text_age
tree_root_1 = render.attach_new_node('empty')
tree_root_2 = render.attach_new_node('empty')
tree_age = 1.0
text_age = OnscreenText(text=str(tree_age), pos=(-0.9, 0.9), scale=0.07)


base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, 0, 4)
base.cam.set_y(-30)
base.add_task(move_camera)
base.accept('1', replace_tree, extraArgs=[BoringTree, 0])
base.accept('shift-1', replace_tree, extraArgs=[BoringTree])
base.accept('r', change_tree_age, extraArgs=[0.1])
base.accept('f', change_tree_age, extraArgs=[-0.1])


# plight = PointLight('plight')
# plight.setColor((0.8, 0.8, 0.8, 1))
# plnp = render.attachNewNode(plight)
# plnp.setPos(10, 20, 30)
# render.setLight(plnp)
# 
# 
# alight = AmbientLight('alight')
# alight.setColor((0.2, 0.2, 0.2, 1))
# alnp = render.attachNewNode(alight)
# render.setLight(alnp)

#from panda3d.core import ShadeModelAttrib
#render.set_attrib(ShadeModelAttrib.make(ShadeModelAttrib.M_flat))
replace_tree(tree_def=BoringTree, seed=0)
base.run()
