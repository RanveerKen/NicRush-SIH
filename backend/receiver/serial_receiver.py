import json
import logging
import sys
from typing import Any

import requests
import serial
from serial import SerialException


# ============================================================
# CONFIGURATION
# ============================================================

# Your receiver ESP32 is currently detected as /dev/ttyUSB0.
SERIAL_PORT = "/dev/ttyUSB0"

# This must match Serial.begin(...) on the ESP32.
BAUD_RATE = 115200

# Serial read timeout in seconds.
SERIAL_TIMEOUT = 2

# FastAPI is running on the same Raspberry Pi.
API_URL = "http://127.0.0.1:8000/api/telemetry"


# ============================================================
# EXPECTED JSON FIELDS
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
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("nicrush-serial")


# ============================================================
# VALIDATION
# ============================================================

def validate_packet(
    packet: dict[str, Any],
) -> tuple[bool, str]:
    """
    Check that the received JSON contains the fields
    expected by the FastAPI backend.
    """

    missing_fields = (
        REQUIRED_FIELDS - packet.keys()
    )

    if missing_fields:
        return (
            False,
            "Missing fields: "
            + ", ".join(
                sorted(missing_fields)
            ),
        )

    # These values must be numeric.
    numeric_fields = (
        "flow_rate",
        "water_distance_cm",
        "vibration",
    )

    for field in numeric_fields:

        value = packet[field]

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

    # drain_id must be text.
    if not isinstance(
        packet["drain_id"],
        str,
    ):
        return (
            False,
            "drain_id must be a string",
        )

    # timestamp must be text.
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
# JSON PARSER
# ============================================================

def parse_json_line(
    line: str,
) -> dict[str, Any] | None:
    """
    Convert one serial line into a Python dictionary.

    The ESP32 must send one complete JSON object per line.
    """

    line = line.strip()

    if not line:
        return None

    try:

        packet = json.loads(line)

    except json.JSONDecodeError as exc:

        logger.warning(
            "Rejected invalid JSON: %s | line=%r",
            exc,
            line,
        )

        return None

    if not isinstance(
        packet,
        dict,
    ):

        logger.warning(
            "Rejected JSON: root object is not a JSON object."
        )

        return None

    valid, reason = validate_packet(
        packet
    )

    if not valid:

        logger.warning(
            "Rejected packet: %s | packet=%s",
            reason,
            packet,
        )

        return None

    return packet


# ============================================================
# SEND PACKET TO FASTAPI
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

        backend_data = response.json()

        logger.info(
            "Backend accepted packet | "
            "node=%s | configured=%s | "
            "DCHI=%s | status=%s",
            backend_data.get(
                "drain_id",
                packet.get("drain_id"),
            ),
            backend_data.get(
                "configured"
            ),
            backend_data.get(
                "dchi"
            ),
            backend_data.get(
                "status"
            ),
        )

    except requests.exceptions.ConnectionError:

        logger.error(
            "Could not connect to FastAPI at %s. "
            "Is Uvicorn running?",
            API_URL,
        )

    except requests.exceptions.Timeout:

        logger.error(
            "FastAPI request timed out."
        )

    except requests.exceptions.HTTPError as exc:

        logger.error(
            "FastAPI rejected packet: %s | response=%s",
            exc,
            getattr(
                exc.response,
                "text",
                "",
            ),
        )

    except requests.RequestException as exc:

        logger.error(
            "Backend request failed: %s",
            exc,
        )

    except ValueError:

        logger.error(
            "Backend returned a response "
            "that was not valid JSON."
        )


# ============================================================
# MAIN SERIAL LOOP
# ============================================================

def main() -> None:

    logger.info(
        "Starting NicRush serial receiver."
    )

    logger.info(
        "Serial port: %s",
        SERIAL_PORT,
    )

    logger.info(
        "Baud rate: %s",
        BAUD_RATE,
    )

    logger.info(
        "Backend API: %s",
        API_URL,
    )

    try:

        with serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=SERIAL_TIMEOUT,
        ) as connection:

            logger.info(
                "Receiver ESP32 connected successfully."
            )

            while True:

                raw_line = (
                    connection.readline()
                )

                if not raw_line:
                    continue

                line = raw_line.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if not line:
                    continue

                logger.info(
                    "Serial RX: %s",
                    line,
                )

                packet = parse_json_line(
                    line
                )

                if packet is None:
                    continue

                logger.info(
                    "Accepted JSON packet: %s",
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

    except FileNotFoundError:

        logger.error(
            "Serial device %s does not exist.",
            SERIAL_PORT,
        )

        logger.error(
            "Check the device with: "
            "ls /dev/ttyUSB* /dev/ttyACM*"
        )

        sys.exit(1)

    except PermissionError:

        logger.error(
            "Permission denied for %s.",
            SERIAL_PORT,
        )

        logger.error(
            "Your user may need access to the "
            "'dialout' group."
        )

        sys.exit(1)

    except SerialException as exc:

        logger.error(
            "Could not open serial port %s: %s",
            SERIAL_PORT,
            exc,
        )

        sys.exit(1)

    except KeyboardInterrupt:

        logger.info(
            "Serial receiver stopped by user."
        )


if __name__ == "__main__":
    main()
