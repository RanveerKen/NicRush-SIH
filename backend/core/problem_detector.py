from backend.core.models import DCHIResult


PROBLEM_MESSAGES = {
    "flow": "ABNORMAL FLOW",
    "water_level": "HIGH WATER LEVEL",
    "vibration": "HIGH VIBRATION",
}


def determine_primary_problem(
    result: DCHIResult,
) -> str:

    scores = {
        "flow": result.scores.flow,
        "water_level": result.scores.water_level,
        "vibration": result.scores.vibration,
    }

    highest_problem = max(
        scores,
        key=scores.get,
    )

    return PROBLEM_MESSAGES[highest_problem]
