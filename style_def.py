from panda3d.core import VBase4


class Skeleton:
    # XY indicator on stem
    x          = VBase4(1, 0, 0, 1)
    y          = VBase4(0, 1, 0, 1)
    xyz_at_top = True  # If False, indicators are at the stem bottom.
    # skeleton geometry
    stem       = VBase4(1, 1, 1, 1)
    # "bark"
    ring_segs  = 10     # Must be set if either ring or bark are used.
    ring       = VBase4(0.7, 0.7, 0.7, 1)
    bark       = False 


class Bark:
    # XY indicator on stem
    x          = False
    y          = False
    xyz_at_top = False
    # skeleton geometry
    stem       = False
    # "bark"
    ring_segs  = 10
    ring       = False
    bark       = VBase4(0.4, 0.1, 0.1, 1)
