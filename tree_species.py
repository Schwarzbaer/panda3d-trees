from tree_specs import StemDefinition as sd
from blending_functions import noisy_linear_length
from blending_functions import boring_radius
from blending_functions import s_curvature
from blending_functions import constant
from blending_functions import linear
from blending_functions import error_smoothing
from blending_functions import linear_split_angle
from blending_functions import branch_density
from blending_functions import func_curvature
from blending_functions import branch_length_function
from blending_functions import equal_split_rotation_func

# FIXME: Move to species definitions file
BoringWillowish = {
    sd.NAME: "Willowish Trunk",
    sd.SEGMENTS: 10,
    sd.LENGTH: noisy_linear_length(1, 8, 0),
    sd.RADIUS: boring_radius(0.5, 0.1),
    sd.BENDING: s_curvature(
        45,                # Lower curvature
        -60,               # Higher curvature
        600,               # Curvature noisiness
        600,               # Noisiness along the other axis
        constant(0.0),     # Twist
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
    sd.SPLIT_CHANCE: error_smoothing(constant(0.1)),
    sd.SPLIT_ANGLE: equal_split_rotation_func(linear(80.0, 20.0)),
    sd.BRANCH_DENSITY: branch_density(linear(10.5, 0.5)),  #constant(20.0)),
    sd.HELIOTROPISM: constant(0.0),
    sd.CHILD_DEFINITION: {
        sd.NAME: "Willowish Branch",
        sd.SEGMENTS: 5,
        sd.LENGTH: branch_length_function(linear(2.0, 3.0)),
        sd.BRANCH_ANGLE: linear(90.0, 30.0),
        sd.BRANCH_ROTATION: noisy_linear_length(0.0, 0.0, 180.0),
        sd.RADIUS: constant(0.04),
        sd.BENDING: func_curvature(constant(0.0), constant(0.0), constant(0.0)),
        sd.HELIOTROPISM: constant(0.3),
    },
}

BoringFirish = {
    sd.NAME: "Firish Trunk",
    sd.SEGMENTS: 10,
    sd.LENGTH: noisy_linear_length(1, 8, 0),
    sd.RADIUS: boring_radius(0.3, 0.1),
    sd.BENDING: s_curvature(
        0,                 # Lower curvature
        0,                 # Higher curvature
        10,                # Curvature noisiness
        10,                # Noisiness along the other axis
        constant(0.0),     # Twist
        linear(0.2, 1.0),  # Age-based magnitude of the overall effect
    ),
    sd.BRANCH_DENSITY: branch_density(linear(10.5, 0.5)),  #constant(20.0)),
    sd.CHILD_DEFINITION: {
        # sd.NAME: "Firish Branch",
        sd.SEGMENTS: 1,
        sd.LENGTH: branch_length_function(linear(3.0, 1.0)),
        sd.BRANCH_ANGLE: linear(90.0, 30.0),
        sd.BRANCH_ROTATION: noisy_linear_length(0.0, 0.0, 180.0),
        sd.RADIUS: constant(0.04),
        sd.BENDING: func_curvature(constant(0.0), constant(0.0), constant(0.0)),
    },
}

BoringBoringish = {
    sd.NAME: "Trunk",
    sd.SEGMENTS: 10,
    sd.LENGTH: constant(10.0),
    sd.RADIUS: constant(0.1),
    sd.SPLIT_CHANCE: error_smoothing(constant(0.15)),
    sd.SPLIT_ANGLE: equal_split_rotation_func(linear(80.0, 20.0), ),
    sd.BENDING: func_curvature(constant(0.0), constant(0.0), constant(0.0)),
    sd.HELIOTROPISM: constant(0.0),
}
