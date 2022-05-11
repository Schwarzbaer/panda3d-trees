import math
from math import pi


def conical(ratio):
    return 0.2 + 0.8 * ratio
def spherical(ratio):
    return 0.2 + 0.8 * math.sin(pi * ratio)
def hemispherical(ratio):
    return 0.2 + 0.8 * math.sin(0.5 * pi * ratio)
def cylindrical(ratio):
    return 1.0
def tapered_cylindrical(ratio):
    return 0.5 + 0.5 * ratio
def flame(ratio):
    if ratio <= 0.7:
        return ratio / 0.7
    else:
        return (1.0 - ratio) / 0.3
def inverse_conical(ratio):
    return 1.0 - 0.8 * ratio
def tend_flame(ratio):
    if ratio <= 0.7:
        return 0.5 + 0.5 * ratio / 0.7
    else:
        return 0.5 + 0.5 * (1.0 - ratio) / 0.3


class SegmentType(Enum):
    STEM = 0
    LEAF = 1


class SplitRotation(Enum):
    HELICAL = 0
    COPLANAR = 1


# Boring Tree, used for debugging.
# Might also makes a good start for new trees.
# child_definition hierarchy:
#   BoringTree -> BoringBranch -> BoringTwig -> BoringLeaf

class BoringLeaf:
    segment_type      = SegmentType.LEAF
    segments          = 0


class BoringTwig:
    segment_type      = SegmentType.STEM
    shape             = None
    taper             = 1.0
    flare             = 0.0
    lobes             = 0
    lobe_depth        = 0.0
    segments          = 10
    #length            = 20.0
    #length_var        =  0.0
    length_base       =  0.0
    trunk_splits      = False
    splits            =  0.0
    split_angle       =  0.0
    split_angle_var   =  0.0
    split_tree_z      =  1.0
    child_rotate_mode = SplitRotation.HELICAL
    child_rotate      =  0.0
    child_rotate_var  =  0.0
    bend              =  0.0
    bend_back         = False
    bend_var          =  0.0
    upward_attraction =  0.0
    diameter          =  1.0
    diameter_var      =  0.0
    child_definition  = None  # BoringLeaf
    child_scale       =  0.5


class BoringBranch:
    segment_type         = SegmentType.STEM
    shape                = None
    taper                = 1.0
    flare                = 0.0
    lobes                = 0
    lobe_depth           = 0.0
    segments             = 10
    #length               = 20.0
    #length_var           =  0.0
    length_base          =  0.0
    trunk_splits         = False
    splits               =  0.0
    split_angle          =  0.0
    split_angle_var      =  0.0
    split_tree_z         =  1.0
    child_rotate_mode    = SplitRotation.HELICAL
    child_rotate         =  0.0
    child_rotate_var     =  0.0
    bend                 =  0.0
    bend_back            = False
    bend_var             =  0.0
    upward_attraction    =  0.0
    diameter             =  1.0
    diameter_var         =  0.0
    child_definition     = None  # BoringTwig
    child_scale          =  0.5
    child_diameter_power =  2.0


class BoringTree:
    segment_type         = SegmentType.STEM        # Is this a stem, or a leaf? (We coud also add blossoms / fruits here.
    shape                = spherical               # Shape; None for branches
    taper                =  1.0                    # nTaper
    flare                =  0.0                    # Flare
    lobes                =  0                      # Lobes
    lobe_depth           =  0.0                    # LobeDepth
    segments             =  3                      # nCurveRes
    length               = 20.0                    # Scale
    length_var           =  0.0                    # ScaleV
    length_base          =  0.33                   # BaseSize; 0.0 for branches
    trunk_splits         =  1                      # 0BaseSplits
    splits               =  0.0                    # nSegSplits
    split_angle          = 20.0                    # nSplitAngle
    split_angle_var      =  0.0                    # nSplitAngleV
    split_tree_z         =  1.0                    # Ratio of "splits rotate around tree's z"; 0 for debugging, 1 for live
    bend                 =  0.0                    # nCurve
    bend_back            =  0.0                    # nCurveBack; False to deactivate
    bend_var             =  0.0                    # nCurveV
    upward_attraction    =  0.0                    # AttractionUp; should be 0 on trunks, value from paper on stems
    diameter             =  1.0
    diameter_var         =  0.0
    child_branches       = 10                      # nBranches
    child_definition     = BoringBranch            # Stem definition class of the next level
    child_scale          =  0.5                    # nLength
    child_diameter_power =  2.0                    # RatioPower
    child_down           = 60.0                    # (n+1)DownAngle
    child_down_var       =  0.0                    # (n+1)DownAngleV
    child_rotate_mode    = SplitRotation.HELICAL   # (n+1)Rotate>=0: helical, else coplanar
    child_rotate         = 10.0                    # abs((n+1)Rotate)
    child_rotate_var     =  0.0                    # (n+1)RotateV


### Quaking Aspen

class QuakingAspen:
    segment_type      = SegmentType.STEM
    shape             = tend_flame
    taper             =   1
    flare             =   0.6
    lobes             =   5
    lobe_depth        =   0.07
    segments          =   3
    length            =  13.0
    length_var        =   3
    trunk_splits      = False
    splits            =   0.0
    split_angle       =   0.0
    split_angle_var   =   0.0
    split_tree_z      =   1.0
    child_rotate_mode = SplitRotation.HELICAL
    child_rotate      = 140.0
    child_rotate_var  =   0.0
    bend              =   0.0
    bend_back         = False
    bend_var          =  20.0
    upward_attraction =   0.0  # 0.5 on branches
    diameter          =   1.0
    diameter_var      =   0.0
    child_definition  = None


### Black Tupelo

class BlackTupeloBranch:
    segment_type         = SegmentType.STEM
    shape                = None                   # Shape (branch)
    taper                = 1.0                    # 1Taper
    flare                = 0.0                    # Flare (branch)
    lobes                = 0                      # Lobes (branch)
    lobe_depth           = 0.0                    # LobeDepth (branch)
    segments             = 10                     # 1CurveRes
    length               = False                  # Scale (branch)
    length_var           = False                  # ScaleV (branch)
    length_base          = 0.0                    # BaseSize (branch)
    trunk_splits         = False                  # 0BaseSplits (branch)
    splits               =  0.0                   # 1SegSplits
    split_angle          =  0.0                   # 1SplitAngle
    split_angle_var      =  0.0                   # 1SplitAngleV
    split_tree_z         =  1.0                   # n/a
    bend                 =   00                   # 1Curve
    bend_back            =   00                   # 1CurveBack
    bend_var             =   90                   # 1CurveVar
    upward_attraction    =    0.5                 # AttractionUp
    diameter             = False                  # n/a
    diameter_var         = False                  # n/a
    child_definition     = None                   # n/a
    child_branches       =   25                   # 2Branches
    child_scale          =    0.3                 # 1Length
    child_diameter_power =    1.3                 # RatioPower
    child_down           =   30.0                 # 2DownAngle
    child_down_var       =   10.0                 # 2DownAngleV
    child_rotate_mode    = SplitRotation.HELICAL  # 2Rotate: 140 > 0
    child_rotate         =  140.0                 # 2Rotate: abs(140)
    child_rotate_var     =    0.0                 # 2RotateV


class BlackTupelo:
    segment_type         = SegmentType.STEM
    shape                =  tapered_cylindrical   # Shape: 4
    taper                =   1.1                  # 0Taper
    flare                =   1.0                  # Flare
    lobes                =   3                    # Lobe
    lobe_depth           =   0.1                  # LobeDepth
    segments             =  10                    # 0CurveRes
    length               =  23.0                  # Scale
    length_var           =   5.0                  # ScaleV
    length_base          =   0.4                  # BaseSize
    trunk_splits         = False                  # 0BaseSplits
    splits               =   0.0                  # 0SegSplits
    split_angle          =   0.0                  # 0SplitAngle
    split_angle_var      =   0.0                  # 0SplitAngleV
    split_tree_z         =   1.0                  # n/a
    bend                 =   0.0                  # 0Curve
    bend_back            = False                  # 0CurveBack
    bend_var             =  40.0                  # 0CurveV
    upward_attraction    =   0.0                  # AttractionUp (trunk)
    diameter             =   1.0                  # n/a
    diameter_var         =   0.0                  # n/a
    child_definition     = BlackTupeloBranch      # n/a
    child_branches       =   50                   # 1Branches
    child_scale          =    1.0                 # 0Length
    child_diameter_power =    1.3                 # RatioPower
    child_down           =   60.0                 # 1DownAngle
    child_down_var       =  -40.0                 # 1DownAngleV
    child_rotate_mode    = SplitRotation.HELICAL  # 1Rotate: 140 < 0
    child_rotate         =  140.0                 # 1Rotate: abs(140)
    child_rotate_var     =    0.0                 # 1RotateV


### Weeping Willow

class WeepingWillowMiniTwig:
    segment_type      = SegmentType.STEM
    shape             = None                      # Shape (branch)
    taper             = 1.0                       # 3Taper
    flare             = 0.0                       # Flare (branch)
    lobes             = 0                         # Lobes (branch)
    lobe_depth        = 0.0                       # LobeDepth (branch)
    segments          = 1                         # 3CurveRes
    length            = False                     # Scale (branch)
    length_var        = False                     # ScaleV (branch)
    length_base       = 0.0                       # BaseSize (branch)
    trunk_splits      = False                     # 0BaseSplits (branch)
    splits            =  0.0                      # 3SegSplits
    split_angle       =  0.0                      # 3SplitAngle
    split_angle_var   =  0.0                      # 3SplitAngleV
    split_tree_z      =  1.0                      # n/a
    bend              =    0                      # 3Curve
    bend_back         =    0                      # 3CurveBack
    bend_var          =    0                      # 3CurveV
    upward_attraction =   -3.0                    # AttractionUp
    diameter          = False                     # n/a
    diameter_var      = False                     # n/a
    child_definition  = None                      # n/a


class WeepingWillowTwig:
    segment_type      = SegmentType.STEM
    shape             = None                      # Shape (branch)
    taper             = 1.0                       # 2Taper
    flare             = 0.0                       # Flare (branch)
    lobes             = 0                         # Lobes (branch)
    lobe_depth        = 0.0                       # LobeDepth (branch)
    segments          = 12                        # 2CurveRes
    length            = False                     # Scale (branch)
    length_var        = False                     # ScaleV (branch)
    length_base       = 0.0                       # BaseSize (branch)
    trunk_splits      = False                     # 0BaseSplits (branch)
    splits            =  0.2                      # 2SegSplits
    split_angle       = 45.0                      # 2SplitAngle
    split_angle_var   = 20.0                      # 2SplitAngleV
    split_tree_z      =  1.0                      # n/a
    bend              =    0                      # 2Curve
    bend_back         =    0                      # 2CurveBack
    bend_var          =    0                      # 2CurveV
    upward_attraction =   -3.0                    # AttractionUp
    diameter          = False                     # n/a
    diameter_var      = False                     # n/a
    child_definition  = WeepingWillowMiniTwig     # n/a
    child_branches       =  300                   # 3Branches
    child_scale          =    1.5                 # 2Length
    child_diameter_power =    2.0                 # RatioPower
    child_down           =   20.0                 # 3DownAngle
    child_down_var       =   10.0                 # 3DownAngleV
    child_rotate_mode    = SplitRotation.HELICAL  # 3Rotate: 140 > 0
    child_rotate         =  140.0                 # 3Rotate: abs(140)
    child_rotate_var     =    0.0                 # 3RotateV


class WeepingWillowBranch:
    segment_type         = SegmentType.STEM
    shape                = None                   # Shape (branch)
    taper                = 1.0                    # 1Taper
    flare                = 0.0                    # Flare (branch)
    lobes                = 0                      # Lobes (branch)
    lobe_depth           = 0.0                    # LobeDepth (branch)
    segments             = 16                     # 1CurveRes
    length               = False                  # Scale (branch)
    length_var           = False                  # ScaleV (branch)
    length_base          = 0.0                    # BaseSize (branch)
    trunk_splits         = False                  # 0BaseSplits (branch)
    splits               =  0.2                   # 1SegSplits
    split_angle          = 30.0                   # 1SplitAngle
    split_angle_var      = 10.0                   # 1SplitAngleV
    split_tree_z         =  1.0                   # n/a
    bend                 =   40                   # 1Curve
    bend_back            =   80                   # 1CurveBack
    bend_var             =   90                   # 1CurveVar
    upward_attraction    =   -3.0                 # AttractionUp
    diameter             = False                  # n/a
    diameter_var         = False                  # n/a
    child_definition     = WeepingWillowTwig      # n/a
    child_branches       =   10                   # 2Branches
    child_scale          =    0.5                 # 1Length
    child_diameter_power =    2.0                 # RatioPower
    child_down           =   30.0                 # 2DownAngle
    child_down_var       =   10.0                 # 2DownAngleV
    child_rotate_mode    = SplitRotation.COPLANAR # 2Rotate: -120 < 0
    child_rotate         =  120.0                 # 2Rotate: abs(-120)
    child_rotate_var     =   30.0                 # 2RotateV


class WeepingWillow:
    segment_type         = SegmentType.STEM
    shape                =  cylindrical           # Shape: 3
    taper                =    1                   # 0Taper
    flare                =    0.75                # Flare
    lobes                =    9                   # Lobes
    lobe_depth           =    0.03                # LobeDepth
    segments             =    8                   # 0CurveRes
    length               =   15.0                 # Scale
    length_var           =    5.0                 # ScaleV
    length_base          =    0.05                # BaseSize
    trunk_splits         =    2                   # 0BaseSplits
    splits               =    0.1                 # 0SegSplits
    split_angle          =    3.0                 # 0SplitAngle
    split_angle_var      =    0.0                 # 0SplitAngleV
    split_tree_z         =    1.0                 # n/a
    bend                 =    0.0                 # 0Curve
    bend_back            =   20.0                 # 0CurveBack
    bend_var             =  120.0                 # 0CurveV
    upward_attraction    =    0.0                 # AttractionUp (trunk)
    diameter             =    1.0                 # n/a
    diameter_var         =    0.0                 # n/a
    child_definition     = WeepingWillowBranch    # n/a
    child_branches       =   25                   # 1Branches
    child_scale          =    0.8                 # 0Length
    child_diameter_power =    2.0                 # RatioPower
    child_down           =   20.0                 # 1DownAngle
    child_down_var       =   10.0                 # 1DownAngleV
    child_rotate_mode    = SplitRotation.COPLANAR # 1Rotate: -120 < 0
    child_rotate         =  120.0                 # 1Rotate: abs(-120)
    child_rotate_var     =   30.0                 # 1RotateV


### California Black Oak

class CaliforniaBlackOak:
    segment_type      = SegmentType.STEM
    shape             = hemispherical
    taper             =   0.95
    flare             =   1.2
    lobes             =   5
    lobe_depth        =   0.1
    segments          =   8
    length            =  10.0
    length_var        =  10.0
    trunk_splits      =   2
    splits            =   0.4
    split_angle       =  10.0
    split_angle_var   =   0.0
    split_tree_z      =   1.0
    child_rotate_mode = SplitRotation.HELICAL
    child_rotate      =  80.0
    child_rotate_var  =   0.0
    bend              =   0.0
    bend_back         = False
    bend_var          =  90.0
    upward_attraction =   0.0  # 0.8 on branches
    diameter          =   1.0
    diameter_var      =   0.0
    child_definition  = None
