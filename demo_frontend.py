import sys
import random

from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import KeyboardButton
from panda3d.core import PointLight
from panda3d.core import AmbientLight

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText

from homebrew import BoringTree  # QuakingAspen, BlackTupelo, WeepingWillow, CaliforniaBlackOak
from homebrew import sg  # Segment enum
from homebrew import expand_fully
import geometry


def replace_tree(tree_def=BoringTree, seed=None):
    if seed is None:
        seed = random.random()

    global tree_root
    global tree_age
    tree_root.remove_node()

    rng = random.Random(seed)
    tree = {
        sg.DEFINITION: BoringTree,
        sg.RNG_SEED: seed,
        sg.AGE: tree_age,
        sg.HELIOTROPIC_DIRECTION: Vec3(0, 0, 1),
    }
    expand_fully(tree)
    tree_geom_node = geometry.trimesh(tree)
    tree_root = render.attach_new_node(tree_geom_node)
    tree[sg.TREE_ROOT_NODE].reparent_to(tree_root)
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
    base.camera.set_h(base.camera.get_h() + turn)
    old_pitch = base.camera.get_p()
    new_pitch = max(min(old_pitch + pitch, 89.9), -89.9)
    base.camera.set_p(new_pitch)
    return task.cont


def change_tree_age(delta):
    global tree_age
    tree_age += delta
    text_age['text'] = str(tree_age)


# Actual application

ShowBase()


global tree_root
global tree_age
global text_age
tree_root = render.attach_new_node('empty')
tree_age = 1.0
text_age = OnscreenText(text=str(tree_age), pos=(-0.9, 0.9), scale=0.07)


base.disable_mouse()
base.accept('escape', sys.exit)
base.camera.set_pos(0, 0, 4)
base.cam.set_y(-20)
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
