import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "nicrush.db"
)


def connect() -> sqlite3.Connection:

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:

    connection = connect()

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                drain_id TEXT PRIMARY KEY,

                pipe_depth_cm REAL NOT NULL,

                sensor_offset_cm REAL NOT NULL
                    DEFAULT 0,

                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS latest_readings (
                drain_id TEXT PRIMARY KEY,

                timestamp TEXT NOT NULL,

                flow_rate REAL NOT NULL,

                water_distance_cm REAL NOT NULL,

                vibration REAL NOT NULL,

                pipe_depth_cm REAL NOT NULL,

                water_depth_cm REAL NOT NULL,

                fill_percentage REAL NOT NULL,

                flow_score REAL NOT NULL,

                water_level_score REAL NOT NULL,

                vibration_score REAL NOT NULL,

                average_penalty REAL NOT NULL,

                dchi REAL NOT NULL,

                status TEXT NOT NULL,

                primary_problem TEXT NOT NULL,

                updated_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:

        connection.close()


def save_node(
    drain_id: str,
    pipe_depth_cm: float,
    sensor_offset_cm: float,
    updated_at: str,
) -> None:

    connection = connect()

    try:

        connection.execute(
            """
            INSERT INTO nodes (
                drain_id,
                pipe_depth_cm,
                sensor_offset_cm,
                updated_at
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(drain_id)
            DO UPDATE SET

                pipe_depth_cm =
                    excluded.pipe_depth_cm,

                sensor_offset_cm =
                    excluded.sensor_offset_cm,

                updated_at =
                    excluded.updated_at
            """,
            (
                drain_id,
                pipe_depth_cm,
                sensor_offset_cm,
                updated_at,
            ),
        )

        connection.commit()

    finally:

        connection.close()


def get_node(
    drain_id: str,
) -> dict | None:

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

        return (
            None
            if row is None
            else dict(row)
        )

    finally:

        connection.close()


def get_nodes() -> list[dict]:

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


def save_latest(
    data: dict,
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
                vibration_score,
                average_penalty,
                dchi,
                status,
                primary_problem,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
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

                vibration_score =
                    excluded.vibration_score,

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
                data["vibration_score"],
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


def get_latest(
    drain_id: str,
) -> dict | None:

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

        return (
            None
            if row is None
            else dict(row)
        )

    finally:

        connection.close()


def get_all_latest() -> list[dict]:

    connection = connect()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM latest_readings
            ORDER BY dchi ASC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()
