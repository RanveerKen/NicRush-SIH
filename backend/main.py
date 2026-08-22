from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.core.dchi import calculate_dchi
from backend.core.models import SensorData
from backend.core.problem_detector import (
    determine_primary_problem,
)


app = FastAPI(
    title="NicRush DCHI",
    description="Drainage Capacity Health Index",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

FRONTEND_FILE = (
    PROJECT_ROOT / "frontend" / "index.html"
)


latest_result: dict[str, Any] = {
    "drain_id": "DRAIN_01",
    "raw": {
        "flow_rate": 0.0,
        "water_level": 0.0,
        "vibration": 0.0,
    },
    "scores": {
        "flow": 0.0,
        "water_level": 0.0,
        "vibration": 0.0,
    },
    "dchi": 100.0,
    "status": "HEALTHY",
    "primary_problem": "NO DATA",
}


data_lock = Lock()


@app.get("/")
def dashboard():

    return FileResponse(
        FRONTEND_FILE
    )


@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "nicrush-dchi",
    }


@app.get("/api/latest")
def latest():

    with data_lock:
        return latest_result


@app.post("/api/telemetry")
def receive_telemetry(
    packet: dict[str, Any],
):

    global latest_result

    sensor_data = SensorData(
        drain_id=str(
            packet["drain_id"]
        ),

        flow_rate=float(
            packet["flow_rate"]
        ),

        water_level=float(
            packet["water_level"]
        ),

        vibration=float(
            packet["vibration"]
        ),
    )

    result = calculate_dchi(
        sensor_data
    )

    primary_problem = (
        determine_primary_problem(
            result
        )
    )

    latest_result = {
        "drain_id": result.drain_id,

        "raw": {
            "flow_rate": result.flow_rate,
            "water_level": result.water_level,
            "vibration": result.vibration,
        },

        "scores": {
            "flow": result.scores.flow,
            "water_level": result.scores.water_level,
            "vibration": result.scores.vibration,
        },

        "dchi": result.dchi,

        "status": result.status,

        "primary_problem": primary_problem,
    }

    return latest_result
