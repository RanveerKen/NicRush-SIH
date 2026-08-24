from backend.core.models import (
    DCHIResult,
    StandardizedScores,
    TelemetryData,
)

from backend.core.standardization import (
    standardize_flow,
    standardize_vibration,
    standardize_water_level,
)


def classify_dchi(
    dchi: float,
) -> str:

    if dchi >= 80:
        return "HEALTHY"

    if dchi >= 50:
        return "MONITOR"

    return "PRIORITY"


def calculate_dchi(
    telemetry: TelemetryData,
    pipe_depth_cm: float,
) -> DCHIResult:

    if pipe_depth_cm <= 0:
        raise ValueError(
            "Pipe depth must be greater than zero."
        )

    # --------------------------------------------------------
    # Convert ultrasonic distance to water depth.
    # --------------------------------------------------------

    water_depth_cm = (
        pipe_depth_cm
        - telemetry.water_distance_cm
    )

    # Prevent impossible negative/overfilled values.

    water_depth_cm = max(
        0.0,
        min(
            water_depth_cm,
            pipe_depth_cm,
        ),
    )

    # --------------------------------------------------------
    # Convert to pipe fill percentage.
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
    # Standardize each sensor.
    # --------------------------------------------------------

    flow_score = standardize_flow(
        telemetry.flow_rate
    )

    water_level_score = (
        standardize_water_level(
            fill_percentage
        )
    )

    vibration_score = (
        standardize_vibration(
            telemetry.vibration
        )
    )

    scores = StandardizedScores(
        flow=flow_score,
        water_level=water_level_score,
        vibration=vibration_score,
    )

    # --------------------------------------------------------
    # Average the three penalty scores.
    # --------------------------------------------------------

    average_penalty = (
        flow_score
        + water_level_score
        + vibration_score
    ) / 3.0

    average_penalty = round(
        average_penalty,
        2,
    )

    # --------------------------------------------------------
    # DCHI
    # --------------------------------------------------------

    dchi = round(
        100.0 - average_penalty,
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
