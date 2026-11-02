"""Funnel stage: whether a buyer is learning, comparing or choosing.

The tool covers only comparing and choosing. One rule marks both answer-key questions (milestone 1)
and topics (milestone 2), so the two milestones count the same thing.
"""

from pathlib import Path

from cgm import claude

STAGES = ["learning", "comparing", "choosing"]

SCHEMA = {"type": "object", "properties": {"stages": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "integer"}, "stage": {"type": "string", "enum": STAGES}},
    "required": ["id", "stage"]}}}, "required": ["stages"]}

PROMPT = """Each numbered item below is a buyer's search question, or a group of search phrases
about one topic. Mark the stage of the buyer who searches it:
- learning: finding out about the problem or the activity, not yet weighing what to buy ("what is
  piano notation", "how do piano lessons work"), including how to do a task in a provider or tool
  the buyer already uses ("how to book a lesson in the acme app");
- comparing: weighing options or whether to buy at all ("best piano schools", "online vs in-person
  piano lessons", "are piano lessons worth it");
- choosing: deciding on a provider or ready to buy ("acme piano school prices", "acme
  alternatives", "piano lessons near me", "how much do piano lessons cost"), including what one
  named provider offers or how it can be trusted ("does acme teach jazz", "is acme any good").

Items:
{items}"""


def mark(items: list[str], model: str, trace: Path, label: str) -> list[str]:
    """Each item's stage, in order; "unknown" when Claude gave none. Only "learning" is dropped,
    so an unknown item is kept."""
    listing = "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
    answer = claude.ask(PROMPT.format(items=listing), SCHEMA, model, trace, label)
    got = {v["id"]: v["stage"] for v in answer["stages"] if 1 <= v["id"] <= len(items)}
    return [got.get(n, "unknown") for n in range(1, len(items) + 1)]


def kept(stage: str) -> bool:
    return stage != "learning"
