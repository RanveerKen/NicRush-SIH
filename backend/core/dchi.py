from backend.core.models import (
    DCHIResult,
    StandardizedScores,
    TelemetryData,
)

from backend.core.standardization import (
    standardize_blockage,
    standardize_flow,
    standardize_water_level,
)


# ============================================================
# DCHI STATUS
# ============================================================

def classify_dchi(
    dchi: float,
) -> str:

    if dchi >= 80.0:
        return "HEALTHY"

    if dchi >= 50.0:
        return "MONITOR"

    return "PRIORITY"


# ============================================================
# DCHI ENGINE
# ============================================================

def calculate_dchi(
    telemetry: TelemetryData,
    pipe_depth_cm: float,
) -> DCHIResult:

    if pipe_depth_cm <= 0:
        raise ValueError(
            "Pipe depth must be greater than zero."
        )


    # --------------------------------------------------------
    # WATER DEPTH
    # --------------------------------------------------------
    #
    # Ultrasonic sensor measures:
    #
    #     sensor -> water surface
    #
    # Therefore:
    #
    #     water depth =
    #         pipe depth - sensor distance
    #
    # --------------------------------------------------------

    water_depth_cm = (
        pipe_depth_cm
        - telemetry.water_distance_cm
    )


    # Clamp physically impossible values.

    water_depth_cm = max(
        0.0,
        min(
            water_depth_cm,
            pipe_depth_cm,
        ),
    )


    # --------------------------------------------------------
    # PIPE FILL
    # --------------------------------------------------------

    fill_percentage = (
        water_depth_cm
        / pipe_depth_cm
    ) * 100.0


    fill_percentage = max(
        0.0,
        min(
            fill_percentage,
            100.0,
        ),
    )


    # --------------------------------------------------------
    # STANDARDIZE THREE COMPONENTS
    # --------------------------------------------------------

    flow_score = (
        standardize_flow(
            telemetry.flow_rate
        )
    )


    water_level_score = (
        standardize_water_level(
            fill_percentage
        )
    )


    blockage_score = (
        standardize_blockage(
            telemetry.vibration
        )
    )


    scores = StandardizedScores(
        flow=flow_score,
        water_level=water_level_score,
        blockage=blockage_score,
    )


    # --------------------------------------------------------
    # AVERAGE PENALTY
    # --------------------------------------------------------

    average_penalty = (
        flow_score
        + water_level_score
        + blockage_score
    ) / 3.0


    average_penalty = round(
        average_penalty,
        2,
    )


    # --------------------------------------------------------
    # DCHI
    # --------------------------------------------------------

    dchi = round(
        100.0
        - average_penalty,
        2,
    )


    return DCHIResult(
        drain_id=telemetry.drain_id,

        timestamp=telemetry.timestamp,

        flow_rate=telemetry.flow_rate,

        water_distance_cm=(
            telemetry.water_distance_cm
        ),

        vibration=telemetry.vibration,

        pipe_depth_cm=pipe_depth_cm,

        water_depth_cm=round(
            water_depth_cm,
            2,
        ),

        fill_percentage=round(
            fill_percentage,
            2,
        ),

        scores=scores,

        average_penalty=average_penalty,

        dchi=dchi,

        status=classify_dchi(dchi),

        primary_problem="",
    )
