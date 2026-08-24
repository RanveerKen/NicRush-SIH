from dataclasses import dataclass


@dataclass
class TelemetryData:
    drain_id: str
    timestamp: str

    flow_rate: float
    water_distance_cm: float
    vibration: float


@dataclass
class StandardizedScores:
    flow: float
    water_level: float
    vibration: float


@dataclass
class DCHIResult:
    drain_id: str
    timestamp: str

    flow_rate: float
    water_distance_cm: float
    vibration: float

    pipe_depth_cm: float
    water_depth_cm: float
    fill_percentage: float

    scores: StandardizedScores

    average_penalty: float
    dchi: float

    status: str
    primary_problem: str

