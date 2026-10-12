"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Any matching query works — checking that selected_item's id survives
        # into suggest_outfit, not anything about the query itself. Criterion 3.
        "name": "selected item reaches suggest_outfit",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 itself is tested separately, outside run_eval.py — it
        # needs 5 DIFFERENT items, not 5 tries of the same query, and this
        # harness only gives one query per criterion row. Kept here as a
        # diagnostic rerun of the same item, not official evidence.
        "name": "fit card mentions price and platform (diagnostic rerun)",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": None,
    },
    {
        # A query with a price ceiling loose enough to return several
        # listings, so there's more than one price to check per try.
        # Criterion 5.
        "name": "price ceiling respected",
        "query": "vintage under $50",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
