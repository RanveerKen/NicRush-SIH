from dataclasses import dataclass


@dataclass
class SensorData:
    drain_id: str
    flow_rate: float
    water_level: float
    vibration: float


@dataclass
class SensorScores:
    flow: float
    water_level: float
    vibration: float


@dataclass
class DCHIResult:
    drain_id: str

    flow_rate: float
    water_level: float
    vibration: float

    scores: SensorScores

    dchi: float
    status: str
    primary_problem: str
