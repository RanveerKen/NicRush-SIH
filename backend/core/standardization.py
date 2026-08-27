import math


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    """
    Keep a value within the requested range.
    """

    return max(
        minimum,
        min(value, maximum),
    )


# ============================================================
# FLOW STANDARDIZATION
# ============================================================
#
# Prototype flow-risk curve:
#
#   0 L/min   -> 100 penalty
#   10 L/min  ->   0 penalty  (nominal healthy point)
#   20 L/min  -> 100 penalty
#   >20 L/min -> 100 penalty  (overflow / excessive flow)
#
# The curve is continuous rather than bucketed.
#
# Formula:
#
# penalty =
#     100 * abs(cos(pi * flow / 20))
#
# Therefore values such as:
#
#   7.0
#   7.13
#   8.42
#   9.75
#
# all receive their own 0-100 penalty.
#
# IMPORTANT:
# These are prototype calibration values, not universal
# hydraulic limits for every 9.5 cm drainage pipe.
# ============================================================

FLOW_HEALTHY = 10.0
FLOW_MAX = 20.0


def standardize_flow(
    flow_rate: float,
) -> float:
    """
    Convert flow rate into a 0-100 penalty score.

    Lowest penalty:
        10 L/min

    Highest penalty:
        0 L/min
        20 L/min
        anything above 20 L/min
    """

    # Prevent impossible negative flow values.
    flow_rate = max(
        0.0,
        flow_rate,
    )

    # --------------------------------------------------------
    # Overflow / excessive-flow region
    # --------------------------------------------------------

    if flow_rate >= FLOW_MAX:
        return 100.0

    # --------------------------------------------------------
    # Smooth double-ended penalty curve
    # --------------------------------------------------------
    #
    # 0 L/min  -> 100
    # 10 L/min ->   0
    # 20 L/min -> 100
    #
    # Using absolute cosine gives the two-sided curve.
    # --------------------------------------------------------

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
#
# The backend converts:
#
#   pipe depth
#        +
#   ultrasonic distance
#
# into:
#
#   water depth
#   fill percentage
#
# Since fill percentage is already 0-100, it can directly
# represent the water-level penalty.
# ============================================================

def standardize_water_level(
    fill_percentage: float,
) -> float:
    """
    Convert pipe fill percentage into a 0-100
    water-level penalty.
    """

    return round(
        clamp(fill_percentage),
        2,
    )


# ============================================================
# VIBRATION STANDARDIZATION
# ============================================================
#
# Prototype calibration.
#
#   0.0  ->   0 penalty
#   1.0+ -> 100 penalty
#
# This range should eventually be calibrated using your
# actual MPU6050 measurements.
# ============================================================

VIBRATION_MIN = 0.0
VIBRATION_MAX = 1.0


def standardize_vibration(
    vibration: float,
) -> float:
    """
    Convert vibration measurement into a
    0-100 penalty score.
    """

    penalty = (
        (
            vibration
            - VIBRATION_MIN
        )
        / (
            VIBRATION_MAX
            - VIBRATION_MIN
        )
    ) * 100.0

    return round(
        clamp(penalty),
        2,
    )
