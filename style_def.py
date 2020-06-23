from panda3d.core import VBase4


class Debug:
    # XY indicator on stem
    x          = VBase4(1, 0, 0, 1)
    y          = VBase4(0, 1, 0, 1)
    xyz_at_top = True                      # If False, indicators are at the stem bottom.
    # skeleton geometry
    stem       = VBase4(1, 1, 1, 1)        # Central axis of the segment
    ring_segs  = 10                        # Must be set if either ring or bark are used.
    ring       = VBase4(0.7, 0.7, 0.7, 1)  # Color of the horizontal ring around the segment's base
    bark       = False                     # Line art to mock up bark.


class Skeleton:
    # XY indicator on stem
    x          = False
    y          = False
    xyz_at_top = True
    # skeleton geometry
    stem       = VBase4(1, 1, 1, 1)        # Central axis of the segment
    ring_segs  = 0
    ring       = False
    bark       = False                     # Line art to mock up bark.


class Bark:
    x          = False
    y          = False
    xyz_at_top = False
    stem       = False
    ring_segs  = 10
    ring       = False
    bark       = VBase4(0.4, 0.1, 0.1, 1)
