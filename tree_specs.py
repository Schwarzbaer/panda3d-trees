import enum


class StemDefinition(enum.Enum):
    NAME             = 99
    SEGMENTS         =  1  # Number of segments in the stem.
    LENGTH           =  2  # age -> length of the stem
    RADIUS           =  3  # age, ratio along stem length -> diameter
    BENDING          =  4  # age, ratio along stem length -> pitch, roll
    SPLIT_CHANCE     =  5  # ratio, accumlator -> chance, accumlator
    SPLIT_ANGLE      =  6
    CHILD_DEFINITION =  7  # StemDefinition of the next level of branches
    BRANCH_DENSITY   =  8
    BRANCH_ANGLE     =  9  # Pitch angle at which a branch splits off, uses branch point ratio along parent stem
    BRANCH_ROTATION  = 10  # Heading for the same.
    # Tropism weight functions
    DESIGN_TROPISM   = 11
    HELIOTROPISM     = 12


class Segment(enum.Enum):
    # Administrative
    RNG_SEED              =  1  # Seed for the random number generator.
    RNG                   =  2  # The random number generator itself.
    DEFINITION            =  3  # The StemDefinition for this stem.
    # Parameters
    AGE                   =  4
    HELIOTROPIC_DIRECTION =  5
    # Segment hierarchy
    TREE_ROOT             =  6  # The first segment of the tree.
    STEM_ROOT             =  7  # The first segment of the stem.
    CONTINUATIONS         =  8  # Segments that continue the stem.
    BRANCHES              =  9
    PARENT_SEGMENT        = 10  # The segment from which this one sprouts.
    REST_SEGMENTS         = 11  # The number of segments left in the stem, inluding this one.
    # Node hierarchy
    TREE_ROOT_NODE        = 12  # The NodePath representing the tree's starting point.
    NODE                  = 15  # The NodePath attached to the LENGTH_NODE, used solely for orientation
    # Geometry data
    TREE_LENGTH           = 16
    STEM_LENGTH           = 17
    LENGTH                = 18  # Length of the segment
    RADIUS                = 19  # The segment's radius ad the top.
    ROOT_RADIUS           = 20  # Trunk radius at the root node (ratio = 0), present only on the TREE_ROOT
    # Stem splitting
    IS_NEW_SPLIT          = 21  # Is this segment created through stem splitting?
    SPLIT_ACCUMULATOR     = 22  # Rounding error accumulator for splitting; Stored on the stem's root.
    # CLONE_BENDING_DEBT  = 12  # Curvature from a split that needs to be compensated for
    # Branching
    IS_NEW_BRANCH         = 23  # FIXME: Is the ratio along the parent segment
    BRANCH_RATIO          = 24  # Ratio along parent stem where the branch is attached
    # Tropism
    DESIGN_TROPISM        = 25
    DESIGN_TWIST          = 26
    HELIOTROPISM          = 27  # 
