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


class SplitRotation(Enum):
    HELICAL = 0
    COPLANAR = 1


class BoringTree:
    shape             = cylindrical             # See table
    segments          =  4                      # nCurveRes
    length            = 20.0                    # Scale
    length_var        =  2.0                    # ScaleV
    trunk_splits      = False                   # 0BaseSplits
    splits            =  1.0                    # nSegSplits
    split_angle       = 30.0                    # nSplitAngle
    split_angle_var   =  0.0                    # nSplitAngleV
    split_tree_z      =  1.0                    # Ratio of "splits rotate around tree's z"; 0 for debugging, 1 for live
    split_rotate_mode = SplitRotation.COPLANAR  # nRotate>=0: helical, else coplanar
    split_rotate      =  0.0                    # abs((n+1)Rotate)
    split_rotate_var  =  0.0                    #(n+1)RotateV
    bend              = 45.0                    # nCurve
    bend_back         = False                   # nCurveBack
    bend_var          =  0.0                    # nCurveV
    diameter          =  1.0
    diameter_var      =  0.0


class QuakingAspen:
    shape             = tend_flame
    segments          =   3
    length            =  13.0
    length_var        =   3
    trunk_splits      = False
    splits            =   0.0
    split_angle       =   0.0
    split_angle_var   =   0.0
    split_tree_z      =   1.0
    split_rotate_mode = SplitRotation.HELICAL
    split_rotate      = 140.0
    split_rotate_var  =   0.0
    bend              =   0.0
    bend_back         = False
    bend_var          =  20.0
    diameter          =   1.0
    diameter_var      =   0.0


class BlackTupelo:
    shape             =  tapered_cylindrical
    segments          =  10
    length            =  23.0
    length_var        =   5.0
    trunk_splits      = False
    splits            =   0.0
    split_angle       =   0.0
    split_angle_var   =   0.0
    split_tree_z      =   1.0
    split_rotate_mode = SplitRotation.HELICAL
    split_rotate      = 140.0
    split_rotate_var  =   0.0
    bend              =   0.0
    bend_back         = False
    bend_var          =  40.0
    diameter          =   1.0
    diameter_var      =   0.0


class WeepingWillow:
    shape             =  cylindrical
    segments          =    8
    length            =   15.0
    length_var        =    5.0
    trunk_splits      =    2
    splits            =    0.1
    split_angle       =    3.0
    split_angle_var   =    0.0
    split_tree_z      =    1.0
    split_rotate_mode = SplitRotation.COPLANAR
    split_rotate      =  120.0
    split_rotate_var  =   30.0
    bend              =    0.0
    bend_back         =   20.0
    bend_var          =  120.0
    diameter          =    1.0
    diameter_var      =    0.0


class CaliforniaBlackOak:
    shape             = hemispherical
    segments          =   8
    length            =  10.0
    length_var        =  10.0
    trunk_splits      =   2
    splits            =   0.4
    split_angle       =  10.0
    split_angle_var   =   0.0
    split_tree_z      =   1.0
    split_rotate_mode = SplitRotation.HELICAL
    split_rotate      =  80.0
    split_rotate_var  =   0.0
    bend              =   0.0
    bend_back         = False
    bend_var          =  90.0
    diameter          =   1.0
    diameter_var      =   0.0
