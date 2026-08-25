from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
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
    configure_node,
    discover_node,
    get_all_latest,
    get_history,
    get_latest,
    get_node,
    get_nodes,
    get_priority_queue,
    initialize_database,
    save_history,
    save_latest,
)


app = FastAPI(
    title="NicRush DCHI",
    description="Drainage Capacity Health Index",
    version="2.1.0",
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
    pipe_depth_cm: float = Field(
        gt=0
    )

    sensor_offset_cm: float = Field(
        ge=0,
        default=0
    )


class TelemetryPacket(BaseModel):
    drain_id: str = Field(
        min_length=1,
        max_length=100
    )

    timestamp: str

    flow_rate: float = Field(
        ge=0
    )

    water_distance_cm: float = Field(
        ge=0
    )

    vibration: float = Field(
        ge=0
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
        "version": "2.1.0",
    }


# ==========================================================
# NODE DISCOVERY / CONFIGURATION
# ==========================================================

@app.get("/api/nodes")
def list_nodes():
    """
    Returns every node that has actually sent telemetry.
    """

    return {
        "nodes": get_nodes()
    }


@app.get("/api/nodes/{drain_id}")
def node_details(
    drain_id: str
):
    node = get_node(
        drain_id
    )

    if node is None:
        raise HTTPException(
            status_code=404,
            detail="Node not discovered yet.",
        )

    return node


@app.post(
    "/api/nodes/{drain_id}/config"
)
def configure_discovered_node(
    drain_id: str,
    config: NodeConfiguration,
):
    node = get_node(
        drain_id
    )

    if node is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Node has not sent telemetry yet."
            ),
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    configured = configure_node(
        drain_id=drain_id,
        pipe_depth_cm=(
            config.pipe_depth_cm
        ),
        sensor_offset_cm=(
            config.sensor_offset_cm
        ),
        configured_at=now,
    )

    return {
        "message": (
            "Node configuration saved."
        ),
        "node": configured,
    }


# ==========================================================
# TELEMETRY
# ==========================================================

@app.post("/api/telemetry")
def receive_telemetry(
    packet: TelemetryPacket,
):
    now = datetime.now(
        timezone.utc
    ).isoformat()

    # ------------------------------------------------------
    # DISCOVER OR UPDATE NODE
    # ------------------------------------------------------

    node = discover_node(
        drain_id=packet.drain_id,
        timestamp=packet.timestamp,
    )

    configured = (
        node["pipe_depth_cm"]
        is not None
    )

    # ------------------------------------------------------
    # UNCONFIGURED NODE
    #
    # We still save the raw telemetry to history/latest.
    # But DCHI cannot be calculated yet.
    # ------------------------------------------------------

    if not configured:

        empty_data = {
            "drain_id": packet.drain_id,
            "timestamp": packet.timestamp,

            "flow_rate": packet.flow_rate,

            "water_distance_cm": (
                packet.water_distance_cm
            ),

            "vibration": packet.vibration,

            "pipe_depth_cm": None,
            "water_depth_cm": None,
            "fill_percentage": None,

            "flow_score": None,
            "water_level_score": None,
            "vibration_score": None,

            "average_penalty": None,
            "dchi": None,

            "status": "CONFIG_REQUIRED",

            "primary_problem": (
                "PLEASE ENTER DEPTH FIRST"
            ),
        }

        save_latest(
            {
                **empty_data,
                "updated_at": now,
            }
        )

        save_history(
            {
                **empty_data,
                "received_at": now,
            }
        )

        return {
            "drain_id": packet.drain_id,
            "discovered": True,
            "configured": False,
            "status": "CONFIG_REQUIRED",
            "message": (
                "Node discovered. "
                "Please enter pipe depth."
            ),
        }

    # ------------------------------------------------------
    # CONFIGURED NODE
    # ------------------------------------------------------

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

    result = calculate_dchi(
        telemetry=telemetry,
        pipe_depth_cm=effective_pipe_depth,
    )

    result.primary_problem = (
        determine_primary_problem(
            result
        )
    )

    ranked_problems = rank_problems(
        result
    )

    common_data = {

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
    }

    # ------------------------------------------------------
    # CURRENT READING
    # ------------------------------------------------------

    save_latest(
        {
            **common_data,
            "updated_at": now,
        }
    )

    # ------------------------------------------------------
    # HISTORICAL READING
    # ------------------------------------------------------

    save_history(
        {
            **common_data,
            "received_at": now,
        }
    )

    return {
        "discovered": True,
        "configured": True,

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
            "flow": (
                result.scores.flow
            ),

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


# ==========================================================
# LATEST
# ==========================================================

@app.get("/api/latest")
def latest(
    drain_id: str | None = None
):
    if drain_id is None:

        nodes = get_nodes()

        if not nodes:

            return {
                "status":
                    "NO_NODES_DISCOVERED",
                "nodes": [],
            }

        # First discovered node for
        # single-node convenience.
        drain_id = nodes[0]["drain_id"]

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
def latest_all():

    return {
        "readings":
            get_all_latest()
    }


# ==========================================================
# PRIORITY QUEUE
# ==========================================================

@app.get("/api/priority")
def priority_queue():

    priority = (
        get_priority_queue()
    )

    numbered = []

    for index, item in enumerate(
        priority,
        start=1
    ):

        numbered.append(
            {
                "rank": index,
                **item,
            }
        )

    return {
        "priority_queue": numbered
    }


# ==========================================================
# HISTORY
# ==========================================================

@app.get(
    "/api/history/{drain_id}"
)
def history(
    drain_id: str,
    limit: int = Query(
        default=500,
        ge=1,
        le=5000,
    ),
):

    node = get_node(
        drain_id
    )

    if node is None:
        raise HTTPException(
            status_code=404,
            detail="Node not discovered.",
        )

    return {
        "drain_id": drain_id,
        "count": limit,
        "readings": get_history(
            drain_id,
            limit,
        ),
    }
