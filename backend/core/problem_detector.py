from backend.core.models import DCHIResult


# ============================================================
# PROBLEM IDENTIFICATION
# ============================================================

PROBLEM_NAMES = {
    "flow": "FLOW CONDITION",
    "water_level": "HIGH WATER LEVEL",
    "blockage": "POSSIBLE PHYSICAL BLOCKAGE",
}


# ============================================================
# RANK SENSOR PROBLEMS
# ============================================================

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
            "type": PROBLEM_NAMES["blockage"],
            "sensor": "blockage",
            "score": result.scores.blockage,
        },

    ]


    problems.sort(
        key=lambda item: item["score"],
        reverse=True,
    )


    return problems


# ============================================================
# PRIMARY PROBLEM
# ============================================================

def determine_primary_problem(
    result: DCHIResult,
) -> str:

    ranked = rank_problems(
        result
    )

    if not ranked:
        return "NO PROBLEM DATA"

    return ranked[0]["type"]

