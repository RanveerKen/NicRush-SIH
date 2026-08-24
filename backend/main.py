from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.core.dchi import calculate_dchi
from backend.core.models import TelemetryData
from backend.core.problem_detector import (
    determine_primary_problem,
    rank_problems,
)

from backend.database import (
    get_all_latest,
    get_latest,
    get_node,
    get_nodes,
    initialize_database,
    save_latest,
    save_node,
)


app = FastAPI(
    title="NicRush DCHI",
    description="Drainage Capacity Health Index",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

FRONTEND_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "index.html"
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


class NodeConfiguration(BaseModel):

    drain_id: str = Field(
        min_length=1,
        max_length=100,
    )

    pipe_depth_cm: float = Field(
        gt=0,
    )

    sensor_offset_cm: float = Field(
        ge=0,
        default=0,
    )


class TelemetryPacket(BaseModel):

    drain_id: str

    timestamp: str

    flow_rate: float = Field(
        ge=0,
    )

    water_distance_cm: float = Field(
        ge=0,
    )

    vibration: float = Field(
        ge=0,
    )


@app.get("/")
def dashboard():

    return FileResponse(
        FRONTEND_PATH
    )


@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "nicrush-dchi",
	    }


@app.get("/api/nodes")
def list_nodes():

    return {
        "nodes": get_nodes()
    }


@app.post("/api/nodes")
def configure_node(
    config: NodeConfiguration,
):

    now = datetime.now(
        timezone.utc
    ).isoformat()

    save_node(
        drain_id=config.drain_id,
        pipe_depth_cm=config.pipe_depth_cm,
        sensor_offset_cm=(
            config.sensor_offset_cm
        ),
        updated_at=now,
    )

    return {
        "message": "Node configuration saved",
        **config.model_dump(),
        "updated_at": now,
    }


@app.get("/api/nodes/{drain_id}")
def node_details(
    drain_id: str,
):

    node = get_node(
        drain_id
    )

    if node is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"{drain_id} is not configured."
            ),
        )

    return node


@app.post("/api/telemetry")
def receive_telemetry(
    packet: TelemetryPacket,
):

    node = get_node(
        packet.drain_id
    )

    if node is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Node configuration missing "
                f"for {packet.drain_id}."
            ),
        )

    # --------------------------------------------------------
    # The node-specific configuration supplies the pipe depth.
    # --------------------------------------------------------

    effective_pipe_depth = (
        node["pipe_depth_cm"]
        + node["sensor_offset_cm"]
    )

    telemetry = TelemetryData(
        drain_id=packet.drain_id,
        timestamp=packet.timestamp,
        flow_rate=packet.flow_rate,
        water_distance_cm=(
            packet.water_distance_cm
        ),
        vibration=packet.vibration,
    )

    # --------------------------------------------------------
    # Calculate fill %, standardized values and DCHI.
    # --------------------------------------------------------

    result = calculate_dchi(
        telemetry=telemetry,
        pipe_depth_cm=effective_pipe_depth,
    )

    result.primary_problem = (
        determine_primary_problem(result)
    )

    ranked_problems = rank_problems(
        result
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    # --???????------------------------------------------------------
    # API response.
    # --------------------------------------------------------

    output = {

        "drain_id": result.drain_id,

        "timestamp": result.timestamp,

        "configuration": {

            "pipe_depth_cm": (
                node["pipe_depth_cm"]
            ),

            "sensor_offset_cm": (
                node["sensor_offset_cm"]
            ),
        },

        "raw": {

            "flow_rate": result.flow_rate,

            "water_distance_cm": (
                result.water_distance_cm
            ),

            "vibration": result.vibration,
        },

        "derived": {

            "water_depth_cm": (
                result.water_depth_cm
            ),

            "fill_percentage": (
                result.fill_percentage
            ),
        },

        "scores": {

            "flow": result.scores.flow,

            "water_level": (
                result.scores.water_level
            ),

            "vibration": (
                result.scores.vibration
            ),
        },

        "average_penalty": (
            result.average_penalty
        ),

        "dchi": result.dchi,

        "status": result.status,

        "primary_problem": (
            result.primary_problem
        ),

        "problem_ranking": (
            ranked_problems
        ),

        "updated_at": now,
    }

    # --------------------------------------------------------
    # Replace the latest reading for this drain.
    # --------------------------------------------------------

    save_latest(
        {
            "drain_id": result.drain_id,

            "timestamp": result.timestamp,

            "flow_rate": result.flow_rate,

            "water_distance_cm": (
                result.water_distance_cm
            ),

            "vibration": result.vibration,

            "pipe_depth_cm": (
                node["pipe_depth_cm"]
            ),

            "water_depth_cm": (
                result.water_depth_cm
            ),

            "fill_percentage": (
                result.fill_percentage
            ),

            "flow_score": (
                result.scores.flow
            ),

            "water_level_score": (
                result.scores.water_level
            ),

            "vibration_score": (
                result.scores.vibration
            ),

            "average_penalty": (
                result.average_penalty
            ),

            "dchi": result.dchi,

            "status": result.status,

            "primary_problem": (
                result.primary_problem
            ),

            "updated_at": now,
        }
    )

    return output


@app.get("/api/latest")
def latest(
    drain_id: str | None = None,
):
    """
    Return the latest reading.

    If drain_id is supplied:
        return that drain's latest reading.

    If drain_id is omitted:
        return the first configured drain's latest reading.

    This keeps the single-drain prototype simple while allowing
    multiple nodes later.
    """

    if drain_id is None:
        nodes = get_nodes()

        if not nodes:
            return {
                "status": "NO_NODE_CONFIGURED",
                "message": (
                    "Configure at least one drain node."
                ),
            }

        drain_id = nodes[0]["drain_id"]

    reading = get_latest(drain_id)

    if reading is None:
        return {
            "drain_id": drain_id,
            "status": "NO_DATA",
            "message": (
                f"No telemetry received yet for {drain_id}."
            ),
        }

    return reading

    reading = get_latest(
        drain_id
    )

    if reading is None:

        return {
            "drain_id": drain_id,
            "status": "NO_DATA",
        }

    return reading


@app.get("/api/latest/all")
def all_latest():

    return {
        "readings":
            get_all_latest()
    }
