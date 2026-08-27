from dataclasses import dataclass


@dataclass
class TelemetryData:
    drain_id: str
    timestamp: str

    flow_rate: float
    water_distance_cm: float

    # Raw MPU impact RMS in g.
    #
    # Kept under the name "vibration" for compatibility
    # with the current ESP32 packet.
    vibration: float


@dataclass
class StandardizedScores:
    flow: float
    water_level: float
    blockage: float


@dataclass
class DCHIResult:
    drain_id: str
    timestamp: str

    # Raw sensor values
    flow_rate: float
    water_distance_cm: float
    vibration: float

    # Node configuration
    pipe_depth_cm: float

    # Derived water values
    water_depth_cm: float
    fill_percentage: float

    # Standardized 0-100 penalties
    scores: StandardizedScores

    # DCHI calculation
    average_penalty: float
    dchi: float

    # Classification
    status: str
    primary_problem: str

