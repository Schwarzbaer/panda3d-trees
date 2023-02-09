def constant(value):
    def inner(_age, _ratio, _rng):
        return value
    return inner


def linear(v_from, v_to):
    def inner(_age, ratio, _rng):
        return v_from + (v_to - v_from) * ratio
    return inner


def noisy_linear_length(v_from, v_to, v_noise):
    def inner(age, ratio, rng):
        v = v_from + (v_to - v_from) * age
        v += rng.uniform(-1, 1) * v_noise
        return v
    return inner


def boring_radius(v_from, v_to):
    def inner(age, ratio, _rng):
        return (v_from + (v_to - v_from) * ratio) * age
    return inner


def func_curvature(twist_func, pitch_func, curve_func):
    def inner(age, ratio, rng):
        return (
            twist_func(age, ratio, rng),
            pitch_func(age, ratio, rng),
            curve_func(age, ratio, rng),
        )
    return inner


def s_curvature(lower_curve, higher_curve, variation, crumple, twist, age_ratio):
    def inner(age, ratio, rng):
        twist_angle = twist(age, ratio, rng)

        if ratio <= 0.5:
            curve = lower_curve
        else:
            curve = higher_curve
        curve += rng.uniform(-1, 1) * variation
        curve *= age_ratio(age, ratio, rng)

        pitch = rng.uniform(-1, 1) * crumple
        pitch *= age_ratio(age, ratio, rng)
        return (twist_angle, pitch, curve)
    return inner


def linear_split_angle(angle_from, angle_to, angle_variation, age_ratio):
    def inner(age, ratio, rng):
         angle = angle_from + (angle_to - angle_from) * ratio
         angle += rng.uniform(-1, 1) * angle_variation
         angle *= age_ratio(age, ratio, rng)
         return angle
    return inner
    

def constant_splitting_func(chance):
    def inner(ratio, accumulator, rng):
        if rng.random() <= chance:
            splits = 1
        else:
            splits = 0
        return splits, accumulator
    return inner


def error_smoothing(split_chance_func):
    def inner(ratio, accumulator, rng):
        split_chance = split_chance_func(0, ratio, rng)
        split_chance_smoothed = split_chance + accumulator
        # We'll consider the number beore the decimal point as the
        # lower limit for the number of splits, and the one after it as
        # the chance for one more.
        bonus_split_chance = split_chance_smoothed % 1
        if rng.random() <= bonus_split_chance:
            splits = math.ceil(split_chance_smoothed)
        else:
            # Since a lot of negative error may have accumulated, we
            # need to take care not to wind up with a negative number of
            # splits.
            splits = max(0, math.floor(split_chance_smoothed))

        error_correction = splits - split_chance
        accumulator -= error_correction

        return splits, accumulator
    return inner


def branch_density(ratio_func):
    def inner(age, ratio, rng):
        return ratio_func(age, ratio, rng)
    return inner


def branch_length_function(ratio_func):
    def inner(age, ratio, rng):
        return ratio_func(age, ratio, rng)
    return inner


