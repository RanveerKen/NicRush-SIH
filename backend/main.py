from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    FileResponse,
)

from pydantic import (
    BaseModel,
    Field,
)

from backend.core.dchi import (
    calculate_dchi,
)

from backend.core.models import (
    TelemetryData,
)

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


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="NicRush DCHI",
    description="Drainage Capacity Health Index",
    version="2.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FRONTEND
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

FRONTEND_PATH = (
    PROJECT_ROOT
    / "frontend"
    / "index.html"
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup() -> None:

    initialize_database()


# ============================================================
# API MODELS
# ============================================================

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


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/")
def dashboard():

    if not FRONTEND_PATH.exists():

        raise HTTPException(
            status_code=500,
            detail="frontend/index.html not found.",
        )

    return FileResponse(
        FRONTEND_PATH
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "nicrush-dchi",
        "version": "2.2.0",
    }


# ============================================================
# NODE DISCOVERY
# ============================================================

@app.get("/api/nodes")
def list_nodes():

    return {
        "nodes": get_nodes()
    }


@app.get(
    "/api/nodes/{drain_id}"
)
def node_details(
    drain_id: str,
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


# ============================================================
# NODE CONFIGURATION
# ============================================================

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


    if configured is None:

        raise HTTPException(
            status_code=404,
            detail="Node not found.",
        )


    return {
        "message": (
            "Node configuration saved."
        ),

        "node": configured,
    }


# ============================================================
# TELEMETRY
# ============================================================

@app.post("/api/telemetry")
def receive_telemetry(
    packet: TelemetryPacket,
):

    received_at = datetime.now(
        timezone.utc
    ).isoformat()


    # --------------------------------------------------------
    # DISCOVER / UPDATE NODE
    # --------------------------------------------------------

    node = discover_node(
        drain_id=packet.drain_id,
        timestamp=packet.timestamp,
    )


    # --------------------------------------------------------
    # NODE HAS NO DEPTH YET
    # --------------------------------------------------------

    if node["pipe_depth_cm"] is None:

        empty_data = {

            "drain_id":
                packet.drain_id,

            "timestamp":
                packet.timestamp,

            "flow_rate":
                packet.flow_rate,

            "water_distance_cm":
                packet.water_distance_cm,

            "vibration":
                packet.vibration,

            "pipe_depth_cm":
                None,

            "water_depth_cm":
                None,

            "fill_percentage":
                None,

            "flow_score":
                None,

            "water_level_score":
                None,

            "blockage_score":
                None,

            "average_penalty":
                None,

            "dchi":
                None,

            "status":
                "CONFIG_REQUIRED",

            "primary_problem":
                "PLEASE ENTER DEPTH FIRST",
        }


        # ----------------------------------------------------
        # Store raw/latest information even before
        # configuration.
        # ----------------------------------------------------

        save_latest(
            {
                **empty_data,

                "updated_at":
                    received_at,
            }
        )


        save_history(
            {
                **empty_data,

                "received_at":
                    received_at,
            }
        )


        return {

            "discovered":
                True,

            "configured":
                False,

            "drain_id":
                packet.drain_id,

            "status":
                "CONFIG_REQUIRED",

            "message":
                (
                    "Node discovered. "
                    "Please enter pipe depth."
                ),
        }


    # --------------------------------------------------------
    # EFFECTIVE PIPE DEPTH
    # --------------------------------------------------------

    effective_pipe_depth = (
        node["pipe_depth_cm"]
        + node["sensor_offset_cm"]
    )


    # --------------------------------------------------------
    # RAW TELEMETRY OBJECT
    # --------------------------------------------------------

    telemetry = TelemetryData(

        drain_id=
            packet.drain_id,

        timestamp=
            packet.timestamp,

        flow_rate=
            packet.flow_rate,

        water_distance_cm=
            packet.water_distance_cm,

        vibration=
            packet.vibration,
    )


    # --------------------------------------------------------
    # DCHI
    # --------------------------------------------------------

    result = calculate_dchi(
        telemetry=
            telemetry,

        pipe_depth_cm=
            effective_pipe_depth,
    )


    # --------------------------------------------------------
    # PRIMARY PROBLEM
    # --------------------------------------------------------

    result.primary_problem = (
        determine_primary_problem(
            result
        )
    )


    # --------------------------------------------------------
    # PROBLEM RANKING
    # --------------------------------------------------------

    ranked_problems = rank_problems(
        result
    )


    # --------------------------------------------------------
    # DATA USED BY DATABASE
    # --------------------------------------------------------

    processed_data = {

        "drain_id":
            result.drain_id,

        "timestamp":
            result.timestamp,

        "flow_rate":
            result.flow_rate,

        "water_distance_cm":
            result.water_distance_cm,

        "vibration":
            result.vibration,

        "pipe_depth_cm":
            node["pipe_depth_cm"],

        "water_depth_cm":
            result.water_depth_cm,

        "fill_percentage":
            result.fill_percentage,

        "flow_score":
            result.scores.flow,

        "water_level_score":
            result.scores.water_level,

        "blockage_score":
            result.scores.blockage,

        "average_penalty":
            result.average_penalty,

        "dchi":
            result.dchi,

        "status":
            result.status,

        "primary_problem":
            result.primary_problem,
    }


    # --------------------------------------------------------
    # SAVE LATEST
    # --------------------------------------------------------

    save_latest(
        {
            **processed_data,

            "updated_at":
                received_at,
        }
    )


    # --------------------------------------------------------
    # SAVE HISTORY
    # --------------------------------------------------------

    save_history(
        {
            **processed_data,

            "received_at":
                received_at,
        }
    )


    # --------------------------------------------------------
    # API RESPONSE
    # --------------------------------------------------------

    return {

        "discovered":
            True,

        "configured":
            True,

        "drain_id":
            result.drain_id,

        "timestamp":
            result.timestamp,

        "configuration": {

            "pipe_depth_cm":
                node["pipe_depth_cm"],

            "sensor_offset_cm":
                node["sensor_offset_cm"],
        },

        "raw": {

            "flow_rate":
                result.flow_rate,

            "water_distance_cm":
                result.water_distance_cm,

            "impact_rms_g":
                result.vibration,
        },

        "derived": {

            "water_depth_cm":
                result.water_depth_cm,

            "fill_percentage":
                result.fill_percentage,
        },

        "scores": {

            "flow":
                result.scores.flow,

            "water_level":
                result.scores.water_level,

            "blockage":
                result.scores.blockage,
        },

        "average_penalty":
            result.average_penalty,

        "dchi":
            result.dchi,

        "status":
            result.status,

        "primary_problem":
            result.primary_problem,

        "problem_ranking":
            ranked_problems,

        "updated_at":
            received_at,
    }


# ============================================================
# LATEST
# ============================================================

@app.get("/api/latest")
def latest(
    drain_id: str | None = None,
):

    if drain_id is None:

        nodes = get_nodes()


        if not nodes:

            return {
                "status":
                    "NO_NODES_DISCOVERED",

                "nodes":
                    [],
            }


        drain_id = nodes[0][
            "drain_id"
        ]


    reading = get_latest(
        drain_id
    )


    if reading is None:

        return {

            "drain_id":
                drain_id,

            "status":
                "NO_DATA",
        }


    # --------------------------------------------------------
    # Convert database row into the same structure returned
    # by POST /api/telemetry.
    # --------------------------------------------------------

    return {

        "drain_id":
            reading["drain_id"],

        "timestamp":
            reading["timestamp"],

        "configuration": {

            "pipe_depth_cm":
                reading["pipe_depth_cm"],
        },

        "raw": {

            "flow_rate":
                reading["flow_rate"],

            "water_distance_cm":
                reading["water_distance_cm"],

            "impact_rms_g":
                reading["vibration"],
        },

        "derived": {

            "water_depth_cm":
                reading["water_depth_cm"],

            "fill_percentage":
                reading["fill_percentage"],
        },

        "scores": {

            "flow":
                reading["flow_score"],

            "water_level":
                reading["water_level_score"],

            "blockage":
                reading["blockage_score"],
        },

        "average_penalty":
            reading["average_penalty"],

        "dchi":
            reading["dchi"],

        "status":
            reading["status"],

        "primary_problem":
            reading["primary_problem"],

        "updated_at":
            reading["updated_at"],
    }


# ============================================================
# ALL LATEST
# ============================================================

@app.get("/api/latest/all")
def latest_all():

    return {
        "readings":
            get_all_latest()
    }


# ============================================================
# PRIORITY QUEUE
# ============================================================

@app.get("/api/priority")
def priority_queue():

    queue = (
        get_priority_queue()
    )


    numbered = []


    for index, item in enumerate(
        queue,
        start=1,
    ):

        numbered.append(
            {
                "rank":
                    index,

                **item,
            }
        )


    return {
        "priority_queue":
            numbered
    }


# ============================================================
# HISTORY
# ============================================================

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


    readings = get_history(
        drain_id,
        limit,
    )


    return {

        "drain_id":
            drain_id,

        "count":
            len(readings),

        "readings":
            readings,
    }
