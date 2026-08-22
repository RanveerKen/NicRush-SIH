from backend.core.models import (
    DCHIResult,
    SensorData,
    SensorScores,
)


# ==========================================================
# DEMO CALIBRATION RANGES
# ==========================================================
#
# These are temporary prototype values.
# We will replace them with your team's actual calibrated
# sensor operating ranges once the electronics team gives them.
#
# The resulting values are PENALTY scores:
#
# 0   = little/no problem
# 100 = severe problem
# ==========================================================

FLOW_MIN = 0.0
FLOW_MAX = 100.0

WATER_LEVEL_MIN = 0.0
WATER_LEVEL_MAX = 100.0

VIBRATION_MIN = 0.0
VIBRATION_MAX = 1.0


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))


def normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    if maximum <= minimum:
        raise ValueError("Maximum must be greater than minimum.")

    score = ((value - minimum) / (maximum - minimum)) * 100.0

    return clamp(score)


def flow_penalty(flow_rate: float) -> float:
    """
    Prototype assumption:
    lower-than-normal flow indicates poorer drainage performance.

    Therefore the normalized value is inverted.
    """

    normal_score = normalize(
        flow_rate,
        FLOW_MIN,
        FLOW_MAX,
    )

    return round(100.0 - normal_score, 2)


def water_level_penalty(water_level: float) -> float:
    """
    Higher water level = greater drainage stress.
    """

    return round(
        normalize(
            water_level,
            WATER_LEVEL_MIN,
            WATER_LEVEL_MAX,
        ),
        2,
    )


def vibration_penalty(vibration: float) -> float:
    """
    Higher vibration = greater structural/disturbance penalty.
    """

    return round(
        normalize(
            vibration,
            VIBRATION_MIN,
            VIBRATION_MAX,
        ),
        2,
    )


def classify_dchi(dchi: float) -> str:

    if dchi >= 80:
        return "HEALTHY"

    if dchi >= 50:
        return "MONITOR"

    return "PRIORITY"


def calculate_dchi(data: SensorData) -> DCHIResult:

    flow_score = flow_penalty(
        data.flow_rate
    )

    water_level_score = water_level_penalty(
        data.water_level
    )

    vibration_score = vibration_penalty(
        data.vibration
    )

    scores = SensorScores(
        flow=flow_score,
        water_level=water_level_score,
        vibration=vibration_score,
    )

    average_penalty = (
        flow_score
        + water_level_score
        + vibration_score
    ) / 3.0

    dchi = round(
        100.0 - average_penalty,
        2,
    )

    status = classify_dchi(dchi)

    return DCHIResult(
        drain_id=data.drain_id,

        flow_rate=data.flow_rate,
        water_level=data.water_level,
        vibration=data.vibration,

        scores=scores,

        dchi=dchi,
        status=status,

        primary_problem="",
    )
