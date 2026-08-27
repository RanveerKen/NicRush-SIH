import json
import logging
import sys
from typing import Any

import requests
import serial

from serial import SerialException


# ============================================================
# SERIAL CONFIGURATION
# ============================================================

SERIAL_PORT = "/dev/ttyUSB0"

BAUD_RATE = 115200

SERIAL_TIMEOUT = 2


# ============================================================
# FASTAPI
# ============================================================

API_URL = (
    "http://127.0.0.1:8000/api/telemetry"
)


# ============================================================
# REQUIRED JSON FIELDS
# ============================================================

REQUIRED_FIELDS = {

    "drain_id",

    "timestamp",

    "flow_rate",

    "water_distance_cm",

    "vibration",
}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(

    level=logging.INFO,

    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)


logger = logging.getLogger(
    "nicrush-serial"
)


# ============================================================
# VALIDATE PACKET
# ============================================================

def validate_packet(
    packet: dict[str, Any],
) -> tuple[bool, str]:

    missing_fields = (
        REQUIRED_FIELDS
        - packet.keys()
    )


    if missing_fields:

        return (
            False,

            (
                "Missing fields: "
                + ", ".join(
                    sorted(
                        missing_fields
                    )
                )
            ),
        )


    # --------------------------------------------------------
    # Validate numeric values
    # --------------------------------------------------------

    numeric_fields = (

        "flow_rate",

        "water_distance_cm",

        "vibration",
    )


    for field in numeric_fields:

        value = packet[field]


        if isinstance(
            value,
            bool,
        ):

            return (
                False,
                f"{field} must be numeric",
            )


        if not isinstance(
            value,
            (int, float),
        ):

            return (
                False,
                f"{field} must be numeric",
            )


        if value < 0:

            return (
                False,
                f"{field} cannot be negative",
            )


    # --------------------------------------------------------
    # Validate strings
    # --------------------------------------------------------

    if not isinstance(
        packet["drain_id"],
        str,
    ):

        return (
            False,
            "drain_id must be a string",
        )


    if not isinstance(
        packet["timestamp"],
        str,
    ):

        return (
            False,
            "timestamp must be a string",
        )


    return True, "OK"


# ============================================================
# PARSE JSON LINE
# ============================================================

def parse_json_line(
    line: str,
) -> dict[str, Any] | None:

    line = line.strip()


    if not line:
        return None


    try:

        packet = json.loads(
            line
        )

    except json.JSONDecodeError:

        logger.warning(
            "Rejected non-JSON line: %s",
            line,
        )

        return None


    if not isinstance(
        packet,
        dict,
    ):

        logger.warning(
            "Rejected packet: JSON root is not an object."
        )

        return None


    valid, reason = (
        validate_packet(
            packet
        )
    )


    if not valid:

        logger.warning(
            "Rejected JSON packet: %s",
            reason,
        )

        return None


    return packet


# ============================================================
# SEND TO FASTAPI
# ============================================================

def send_to_backend(
    packet: dict[str, Any],
) -> None:

    try:

        response = requests.post(

            API_URL,

            json=packet,

            timeout=5,
        )


        response.raise_for_status()


        result = response.json()


        logger.info(

            "Backend accepted %s | "
            "DCHI=%s | "
            "status=%s | "
            "problem=%s",

            packet["drain_id"],

            result.get("dchi"),

            result.get("status"),

            result.get(
                "primary_problem"
            ),
        )


    except requests.RequestException as exc:

        logger.error(
            "FastAPI request failed: %s",
            exc,
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    logger.info(
        "Starting NicRush serial receiver"
    )


    logger.info(
        "Serial device: %s",
        SERIAL_PORT,
    )


    logger.info(
        "Baud rate: %s",
        BAUD_RATE,
    )


    try:

        with serial.Serial(

            port=SERIAL_PORT,

            baudrate=BAUD_RATE,

            timeout=SERIAL_TIMEOUT,

        ) as connection:


            logger.info(
                "Receiver ESP32 connected."
            )


            # ------------------------------------------------
            # Give the receiver a moment to reset after
            # opening the serial port.
            # ------------------------------------------------

            connection.reset_input_buffer()


            while True:

                raw_line = (
                    connection.readline()
                )


                if not raw_line:
                    continue


                line = raw_line.decode(

                    "utf-8",

                    errors="replace",
                )


                packet = parse_json_line(
                    line
                )


                if packet is None:
                    continue


                logger.info(
                    "Received JSON: %s",
                    json.dumps(
                        packet,
                        separators=(
                            ",",
                            ":",
                        ),
                    ),
                )


                send_to_backend(
                    packet
                )


    except SerialException as exc:

        logger.error(

            "Could not open %s: %s",

            SERIAL_PORT,

            exc,
        )

        sys.exit(1)


    except KeyboardInterrupt:

        logger.info(
            "Serial receiver stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
