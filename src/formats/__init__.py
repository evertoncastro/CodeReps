"""Registry of assessment formats.

A format is a plain module. It owns everything about one kind of assessment:
the layout of a challenge folder, what a "stage" means, which files the
candidate may see, and how an attempt is graded. The core (main.py,
runner_core.py, runs.py) knows only the contract below.

Adding a format: write the module, drop its challenges under
challenges/<ID>/, and add it to _CANDIDATES. Nothing else.

The contract — module-level attributes and functions:

    ID              str   URL segment and DB value; permanent once used
    TITLE           str   shown on the home page
    DESCRIPTION     str   one line, shown on the home page
    STAGE_LABEL     str   display noun for a unit of work ("Level", "Exercise")

    stages(cdir) -> list[int]
        The authored stages, in order.
    stage_doc(cdir, stage) -> str
        The stage's instructions, as markdown.
    files(cdir, unlocked) -> list[dict]
        Explorer entries: {"id", "label", "editable"}.
    stage_of_file(file_id) -> int | None
        The stage a file id is gated behind; None when it is not gated.
    read_file(cdir, file_id) -> str | None
        Content of a whitelisted id. Everything else MUST be unaddressable —
        this is what keeps hidden tests and templates off the wire.
    new_solution(cdir) -> str
        Starter code for a fresh attempt.
    run_stage(cdir, target, code) -> dict
        Grade `code` for `target`. Must return {"passed": bool, ...}; the rest
        of the dict is passed through to the client untouched.

`cdir` is always the challenge directory, so a format never learns how the
library is laid out.
"""

# Ids that would collide with an existing route.
RESERVED_IDS = {"ui", "api", "static", "favicon.ico"}

_CANDIDATES = ("ica", "python_gym")

ALL: list = []
UNAVAILABLE: dict[str, str] = {}

for _name in _CANDIDATES:
    try:
        _module = __import__(f"formats.{_name}", fromlist=["*"])
    except ImportError as exc:  # a format whose dependencies are missing
        UNAVAILABLE[_name] = str(exc)
        continue
    if _module.ID in RESERVED_IDS:
        raise ValueError(f"format id {_module.ID!r} collides with a route")
    ALL.append(_module)

_BY_ID = {m.ID: m for m in ALL}


def get(format_id: str):
    """The format module for this id, or None if unknown/unavailable."""
    return _BY_ID.get(format_id)


def infos() -> list[dict]:
    """Metadata for the home page: every format, available or not.

    A format whose dependencies are missing is still listed — as unavailable,
    with the reason — because silently vanishing from the home page looks like a
    bug in the app rather than a missing package.
    """
    out = [
        {
            "id": m.ID,
            "title": m.TITLE,
            "description": m.DESCRIPTION,
            "stage_label": m.STAGE_LABEL,
            "available": True,
            "unavailable_reason": None,
        }
        for m in ALL
    ]
    out += [
        {
            "id": name.replace("_", "-"),
            "title": name.replace("_", "-"),
            "description": "",
            "stage_label": "Stage",
            "available": False,
            "unavailable_reason": reason,
        }
        for name, reason in UNAVAILABLE.items()
    ]
    return out
