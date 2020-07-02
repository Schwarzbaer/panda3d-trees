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


# Boring Tree, used for debugging. Might also makes a good start for new trees.

class BoringLeaves:
    segment_type      = SegmentType.LEAF
    segments          = 0


class BoringBranch:
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
    child_definition  = None
    child_scale       =  0.5


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
    child_definition  = None
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


# Actual botanical trees

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


class BlackTupelo:
    segment_type      = SegmentType.STEM
    shape             =  tapered_cylindrical
    taper             =   1.1
    flare             =   1.0
    lobes             =   3
    lobe_depth        =   0.1
    segments          =  10
    length            =  23.0
    length_var        =   5.0
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
    bend_var          =  40.0
    upward_attraction =   0.0  # 0.5 on branches
    diameter          =   1.0
    diameter_var      =   0.0
    child_definition  = None


### Weeping Willow

class WeepingWillowBranch:
    segment_type      = SegmentType.STEM
    shape             = None
    taper             = 1.0
    flare             = 0.0
    lobes             = 0
    lobe_depth        = 0.0
    segments          = 16
    length            = False
    length_var        = False
    trunk_splits      = False
    splits            =  0.2
    split_angle       = 45.0
    split_angle_var   = 20.0
    split_tree_z      =  1.0
    child_rotate_mode = SplitRotation.COPLANAR
    child_rotate      = -120.0
    child_rotate_var  =   30.0
    bend              =   40
    bend_back         =   80
    bend_var          =   90
    upward_attraction =   -3.0
    diameter          = False
    diameter_var      = False
    child_definition  = None
    child_scale       = 0.5
    child_scale_var   = 0.1


class WeepingWillow:
    segment_type         = SegmentType.STEM
    shape                =  cylindrical
    taper                =    1
    flare                =    0.75
    lobes                =    9
    lobe_depth           =    0.03
    segments             =    8
    length               =   15.0
    length_var           =    5.0
    length_base          =    0.05
    trunk_splits         =    2
    splits               =    0.1
    split_angle          =    3.0
    split_angle_var      =    0.0
    split_tree_z         =    1.0
    bend                 =    0.0
    bend_back            =   20.0
    bend_var             =  120.0
    upward_attraction    =    0.0
    diameter             =    1.0
    diameter_var         =    0.0
    child_definition     = WeepingWillowBranch
    child_branches       =   25
    child_scale          =    0.8
    child_diameter_power =    2.0
    child_down           =   20.0
    child_down_var       =   10.0
    child_rotate_mode    = SplitRotation.COPLANAR
    child_rotate         =  120.0
    child_rotate_var     =   30.0


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
