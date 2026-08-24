"""
Convert different physical sensor measurements into a common
0-100 PENALTY scale.

0   = little/no drainage degradation
100 = severe drainage degradation

These calibration values are temporary prototype values and
must be replaced with experimentally validated ranges.
"""


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def linear_normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    if maximum <= minimum:
        raise ValueError(
            "maximum must be greater than minimum"
        )

    result = (
        (value - minimum)
        / (maximum - minimum)
    ) * 100.0

    return clamp(result)


# ------------------------------------------------------------
# FLOW
# ------------------------------------------------------------

FLOW_MIN = 0.0
FLOW_MAX = 100.0


def standardize_flow(
    flow_rate: float,
) -> float:
    """
    Prototype assumption:
    lower flow = greater drainage problem.

    Therefore the normalised value is inverted.
    """

    normal_score = linear_normalize(
        flow_rate,
        FLOW_MIN,
        FLOW_MAX,
    )

    penalty = 100.0 - normal_score

    return round(
        clamp(penalty),
        2,
    )


# ------------------------------------------------------------
# WATER LEVEL
# ------------------------------------------------------------

def standardize_water_level(
    fill_percentage: float,
) -> float:
    """
    Fill percentage is already a 0-100 representation.

    For the current prototype:
        fill percentage == water-level penalty
    """

    return round(
        clamp(fill_percentage),
        2,
    )


# ------------------------------------------------------------
# VIBRATION
# ------------------------------------------------------------

VIBRATION_MIN = 0.0
VIBRATION_MAX = 1.0


def standardize_vibration(
    vibration: float,
) -> float:

    penalty = linear_normalize(
        vibration,
        VIBRATION_MIN,
        VIBRATION_MAX,
    )

    return round(
        clamp(penalty),
        2,
    )
