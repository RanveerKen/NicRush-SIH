import sqlite3

from pathlib import Path
from typing import Any


# ============================================================
# DATABASE LOCATION
# ============================================================

DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "nicrush.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect() -> sqlite3.Connection:

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database() -> None:

    connection = connect()

    try:

        # ----------------------------------------------------
        # DISCOVERED NODES
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (

                drain_id TEXT PRIMARY KEY,

                pipe_depth_cm REAL,

                sensor_offset_cm REAL NOT NULL
                    DEFAULT 0,

                discovered_at TEXT NOT NULL,

                configured_at TEXT,

                last_seen TEXT NOT NULL

            )
            """
        )


        # ----------------------------------------------------
        # MOST RECENT READING
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS latest_readings (

                drain_id TEXT PRIMARY KEY,

                timestamp TEXT NOT NULL,

                flow_rate REAL NOT NULL,

                water_distance_cm REAL NOT NULL,

                vibration REAL NOT NULL,

                pipe_depth_cm REAL,

                water_depth_cm REAL,

                fill_percentage REAL,

                flow_score REAL,

                water_level_score REAL,

                blockage_score REAL,

                average_penalty REAL,

                dchi REAL,

                status TEXT NOT NULL,

                primary_problem TEXT NOT NULL,

                updated_at TEXT NOT NULL,

                FOREIGN KEY (drain_id)
                    REFERENCES nodes(drain_id)

            )
            """
        )


        # ----------------------------------------------------
        # COMPLETE TELEMETRY HISTORY
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_history (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                drain_id TEXT NOT NULL,

                timestamp TEXT NOT NULL,

                flow_rate REAL NOT NULL,

                water_distance_cm REAL NOT NULL,

                vibration REAL NOT NULL,

                pipe_depth_cm REAL,

                water_depth_cm REAL,

                fill_percentage REAL,

                flow_score REAL,

                water_level_score REAL,

                blockage_score REAL,

                average_penalty REAL,

                dchi REAL,

                status TEXT NOT NULL,

                primary_problem TEXT NOT NULL,

                received_at TEXT NOT NULL,

                FOREIGN KEY (drain_id)
                    REFERENCES nodes(drain_id)

            )
            """
        )


        # ----------------------------------------------------
        # HISTORY INDEX
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_history_drain_time

            ON telemetry_history (
                drain_id,
                timestamp
            )
            """
        )


        connection.commit()

    finally:

        connection.close()


# ============================================================
# NODE DISCOVERY
# ============================================================

def discover_node(
    drain_id: str,
    timestamp: str,
) -> dict[str, Any]:

    connection = connect()

    try:

        row = connection.execute(
            """
            SELECT *
            FROM nodes
            WHERE drain_id = ?
            """,
            (drain_id,),
        ).fetchone()


        # ----------------------------------------------------
        # EXISTING NODE
        # ----------------------------------------------------

        if row is not None:

            connection.execute(
                """
                UPDATE nodes

                SET last_seen = ?

                WHERE drain_id = ?
                """,
                (
                    timestamp,
                    drain_id,
                ),
            )


            connection.commit()


            row = connection.execute(
                """
                SELECT *
                FROM nodes
                WHERE drain_id = ?
                """,
                (drain_id,),
            ).fetchone()


            return dict(row)


        # ----------------------------------------------------
        # NEW NODE
        # ----------------------------------------------------

        connection.execute(
            """
            INSERT INTO nodes (

                drain_id,
                pipe_depth_cm,
                sensor_offset_cm,
                discovered_at,
                configured_at,
                last_seen

            )

            VALUES (
                ?,
                NULL,
                0,
                ?,
                NULL,
                ?
            )
            """,
            (
                drain_id,
                timestamp,
                timestamp,
            ),
        )


        connection.commit()


        row = connection.execute(
            """
            SELECT *
            FROM nodes
            WHERE drain_id = ?
            """,
            (drain_id,),
        ).fetchone()


        return dict(row)

    finally:

        connection.close()


# ============================================================
# CONFIGURE NODE
# ============================================================

def configure_node(
    drain_id: str,
    pipe_depth_cm: float,
    sensor_offset_cm: float,
    configured_at: str,
) -> dict[str, Any] | None:

    connection = connect()

    try:

        cursor = connection.execute(
            """
            UPDATE nodes

            SET
                pipe_depth_cm = ?,
                sensor_offset_cm = ?,
                configured_at = ?

            WHERE drain_id = ?
            """,
            (
                pipe_depth_cm,
                sensor_offset_cm,
                configured_at,
                drain_id,
            ),
        )


        connection.commit()


        if cursor.rowcount == 0:
            return None


        row = connection.execute(
            """
            SELECT *
            FROM nodes
            WHERE drain_id = ?
            """,
            (drain_id,),
        ).fetchone()


        return dict(row)

    finally:

        connection.close()


# ============================================================
# GET ONE NODE
# ============================================================

def get_node(
    drain_id: str,
) -> dict[str, Any] | None:

    connection = connect()

    try:

        row = connection.execute(
            """
            SELECT *
            FROM nodes
            WHERE drain_id = ?
            """,
            (drain_id,),
        ).fetchone()


        if row is None:
            return None


        return dict(row)

    finally:

        connection.close()


# ============================================================
# GET ALL DISCOVERED NODES
# ============================================================

def get_nodes() -> list[dict[str, Any]]:

    connection = connect()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM nodes
            ORDER BY drain_id
            """
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# SAVE LATEST READING
# ============================================================

def save_latest(
    data: dict[str, Any],
) -> None:

    connection = connect()

    try:

        connection.execute(
            """
            INSERT INTO latest_readings (

                drain_id,
                timestamp,
                flow_rate,
                water_distance_cm,
                vibration,
                pipe_depth_cm,
                water_depth_cm,
                fill_percentage,
                flow_score,
                water_level_score,
                blockage_score,
                average_penalty,
                dchi,
                status,
                primary_problem,
                updated_at

            )

            VALUES (

                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?

            )

            ON CONFLICT(drain_id)

            DO UPDATE SET

                timestamp =
                    excluded.timestamp,

                flow_rate =
                    excluded.flow_rate,

                water_distance_cm =
                    excluded.water_distance_cm,

                vibration =
                    excluded.vibration,

                pipe_depth_cm =
                    excluded.pipe_depth_cm,

                water_depth_cm =
                    excluded.water_depth_cm,

                fill_percentage =
                    excluded.fill_percentage,

                flow_score =
                    excluded.flow_score,

                water_level_score =
                    excluded.water_level_score,

                blockage_score =
                    excluded.blockage_score,

                average_penalty =
                    excluded.average_penalty,

                dchi =
                    excluded.dchi,

                status =
                    excluded.status,

                primary_problem =
                    excluded.primary_problem,

                updated_at =
                    excluded.updated_at

            """,
            (
                data["drain_id"],
                data["timestamp"],
                data["flow_rate"],
                data["water_distance_cm"],
                data["vibration"],
                data["pipe_depth_cm"],
                data["water_depth_cm"],
                data["fill_percentage"],
                data["flow_score"],
                data["water_level_score"],
                data["blockage_score"],
                data["average_penalty"],
                data["dchi"],
                data["status"],
                data["primary_problem"],
                data["updated_at"],
            ),
        )


        connection.commit()

    finally:

        connection.close()


# ============================================================
# SAVE HISTORICAL READING
# ============================================================

def save_history(
    data: dict[str, Any],
) -> None:

    connection = connect()

    try:

        connection.execute(
            """
            INSERT INTO telemetry_history (

                drain_id,
                timestamp,
                flow_rate,
                water_distance_cm,
                vibration,
                pipe_depth_cm,
                water_depth_cm,
                fill_percentage,
                flow_score,
                water_level_score,
                blockage_score,
                average_penalty,
                dchi,
                status,
                primary_problem,
                received_at

            )

            VALUES (

                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?

            )
            """,
            (
                data["drain_id"],
                data["timestamp"],
                data["flow_rate"],
                data["water_distance_cm"],
                data["vibration"],
                data["pipe_depth_cm"],
                data["water_depth_cm"],
                data["fill_percentage"],
                data["flow_score"],
                data["water_level_score"],
                data["blockage_score"],
                data["average_penalty"],
                data["dchi"],
                data["status"],
                data["primary_problem"],
                data["received_at"],
            ),
        )


        connection.commit()

    finally:

        connection.close()


# ============================================================
# GET LATEST READING
# ============================================================

def get_latest(
    drain_id: str,
) -> dict[str, Any] | None:

    connection = connect()

    try:

        row = connection.execute(
            """
            SELECT *
            FROM latest_readings
            WHERE drain_id = ?
            """,
            (drain_id,),
        ).fetchone()


        if row is None:
            return None


        return dict(row)

    finally:

        connection.close()


# ============================================================
# GET ALL LATEST READINGS
# ============================================================

def get_all_latest() -> list[dict[str, Any]]:

    connection = connect()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM latest_readings

            ORDER BY
                CASE
                    WHEN dchi IS NULL THEN 1
                    ELSE 0
                END,

                dchi ASC
            """
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GET HISTORY
# ============================================================

def get_history(
    drain_id: str,
    limit: int = 500,
) -> list[dict[str, Any]]:

    connection = connect()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM telemetry_history

            WHERE drain_id = ?

            ORDER BY
                timestamp DESC

            LIMIT ?
            """,
            (
                drain_id,
                limit,
            ),
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# PRIORITY QUEUE
# ============================================================

def get_priority_queue() -> list[dict[str, Any]]:

    connection = connect()

    try:

        rows = connection.execute(
            """
            SELECT

                l.drain_id,
                l.dchi,
                l.status,
                l.primary_problem,
                l.updated_at

            FROM latest_readings l

            INNER JOIN nodes n
                ON l.drain_id = n.drain_id

            WHERE

                n.pipe_depth_cm IS NOT NULL

                AND l.dchi IS NOT NULL

            ORDER BY
                l.dchi ASC
            """
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()
