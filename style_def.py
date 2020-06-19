from panda3d.core import VBase4


class Skeleton:
    # XY indicator on stem
    x = False # VBase4(1, 0, 0, 1)
    y = False # VBase4(0, 1, 0, 1)
    xyz_at_top = True  # If False, indicators will be at the stem bottom.
    # skeleton geometry
    stem = False  # VBase4(1, 1, 1, 1)
    # "bark"
    ring_segs = 10     # Must be set if either ring or bark are used.
    ring = False # VBase4(0.7, 0.7, 0.7, 1)
    bark = VBase4(0.4, 0.1, 0.1, 1)
