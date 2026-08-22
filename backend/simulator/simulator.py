import json
import random


def normal_scenario() -> dict:

    return {
        "drain_id": "DRAIN_01",

        "flow_rate": round(
            random.uniform(75, 90),
            2,
        ),

        "water_level": round(
            random.uniform(15, 30),
            2,
        ),

        "vibration": round(
            random.uniform(0.05, 0.20),
            2,
        ),
    }


def degraded_scenario() -> dict:

    return {
        "drain_id": "DRAIN_01",

        "flow_rate": round(
            random.uniform(40, 60),
            2,
        ),

        "water_level": round(
            random.uniform(45, 65),
            2,
        ),

        "vibration": round(
            random.uniform(0.30, 0.60),
            2,
        ),
    }


def critical_scenario() -> dict:

    return {
        "drain_id": "DRAIN_01",

        "flow_rate": round(
            random.uniform(10, 30),
            2,
        ),

        "water_level": round(
            random.uniform(75, 95),
            2,
        ),

        "vibration": round(
            random.uniform(0.70, 0.95),
            2,
        ),
    }


def main():

    print()
    print("NicRush DCHI Simulator")
    print("======================")
    print()
    print("n = normal")
    print("d = degraded")
    print("c = critical")
    print("q = quit")
    print()

    while True:

        command = input(
            "Select scenario: "
        ).strip().lower()

        if command == "n":
            packet = normal_scenario()

        elif command == "d":
            packet = degraded_scenario()

        elif command == "c":
            packet = critical_scenario()

        elif command == "q":
            break

        else:
            print("Invalid command.")
            continue

        print()
        print(json.dumps(
            packet,
            indent=2,
        ))
        print()


if __name__ == "__main__":
    main()
