import math


# ============================================================
# GENERAL UTILITY
# ============================================================

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    """
    Keep a value within a specified range.
    """

    return max(
        minimum,
        min(value, maximum),
    )


# ============================================================
# FLOW STANDARDIZATION
# ============================================================
#
# Prototype flow-risk model:
#
#       0 L/min  -> 100 penalty
#      10 L/min  ->   0 penalty
#      20 L/min  -> 100 penalty
#      >20 L/min -> 100 penalty
#
# The curve is continuous.
#
# Formula:
#
# penalty =
#     100 * |cos(pi * flow / 20)|
#
# This means intermediate readings such as:
#
# 7.00
# 7.13
# 8.42
# 9.76
#
# all receive their own 0-100 penalty.
#
# IMPORTANT:
# These are prototype calibration values, not universal
# hydraulic limits for every drain.
# ============================================================

FLOW_HEALTHY = 10.0
FLOW_MAX = 20.0


def standardize_flow(
    flow_rate: float,
) -> float:
    """
    Convert flow rate in L/min into a 0-100
    drainage-risk penalty.

    10 L/min is the nominal healthy point.
    """

    flow_rate = max(
        0.0,
        float(flow_rate),
    )

    # Excessive-flow / overflow region.
    if flow_rate >= FLOW_MAX:
        return 100.0

    penalty = (
        100.0
        * abs(
            math.cos(
                math.pi
                * flow_rate
                / FLOW_MAX
            )
        )
    )

    return round(
        clamp(penalty),
        2,
    )


# ============================================================
# WATER LEVEL STANDARDIZATION
# ============================================================

def standardize_water_level(
    fill_percentage: float,
) -> float:
    """
    Fill percentage is already 0-100.

    For the prototype this directly represents
    the water-level penalty.
    """

    return round(
        clamp(
            float(fill_percentage)
        ),
        2,
    )


# ============================================================
# BLOCKAGE PROBABILITY
# ============================================================
#
# The MPU6050 is mounted on the mechanical rod inside
# the drainage pipe.
#
# The ESP32 currently sends its calculated movement RMS
# through the telemetry field named "vibration".
#
# We interpret that numeric value as impact RMS in g.
#
# Prototype calibration:
#
#     0.00 g ->   0% blockage probability
#     0.10 g -> 100% blockage probability
#
# >0.10 g is capped at 100%.
#
# This is an estimated prototype probability score,
# not a statistically validated probability until
# blocked/unblocked field data is collected.
# ============================================================

BLOCKAGE_RMS_MAX = 0.10


def standardize_blockage(
    rms_g: float,
) -> float:
    """
    Convert impact RMS in g into a 0-100
    estimated blockage probability.
    """

    rms_g = max(
        0.0,
        float(rms_g),
    )

    if rms_g >= BLOCKAGE_RMS_MAX:
        return 100.0

    probability = (
        rms_g
        / BLOCKAGE_RMS_MAX
    ) * 100.0

    return round(
        clamp(probability),
        2,
    )
