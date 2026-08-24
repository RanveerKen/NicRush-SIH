from backend.core.models import DCHIResult


PROBLEM_NAMES = {
    "flow": "ABNORMAL FLOW",
    "water_level": "HIGH WATER LEVEL",
    "vibration": "HIGH VIBRATION",
}


def rank_problems(
    result: DCHIResult,
) -> list[dict]:

    problems = [
        {
            "type": PROBLEM_NAMES["flow"],
            "sensor": "flow",
            "score": result.scores.flow,
        },
        {
            "type": PROBLEM_NAMES["water_level"],
            "sensor": "water_level",
            "score": result.scores.water_level,
        },
        {
            "type": PROBLEM_NAMES["vibration"],
            "sensor": "vibration",
            "score": result.scores.vibration,
        },
    ]

    problems.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return problems


def determine_primary_problem(
    result: DCHIResult,
) -> str:

    ranked = rank_problems(
        result
    )

    return ranked[0]["type"]
