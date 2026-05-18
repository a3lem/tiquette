# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken>=0.8.0"]
# ///
"""
Measure token cost of accomplishing ticket tasks under different CLI designs.

Designs:
  A: status-quo, specific verbs (create, describe, tag, add-note, add-dep, set-prio)
  B: symmetric create/edit with full flag sets, alias verbs kept
  C: minimal `new` (title only) + unified `edit`, no aliases
  D: single mega-command `tq <id|new> [flags]`

Buckets:
  learn: help pages an agent must read to know the surface for the tasks tested
  emit:  the command(s) the agent writes
  read:  stdout the agent reads back

Run:  uv run experiment/cli_verbosity.py
"""

from __future__ import annotations

from dataclasses import dataclass

import tiktoken  # pyright: ignore[reportMissingImports]  # inline script dep

ENCODING = tiktoken.get_encoding("o200k_base")


def n_tok(s: str) -> int:
    return len(ENCODING.encode(s))


# ---------------------------------------------------------------------------
# Help texts (one terse line per flag; same style across designs to isolate
# design from prose verbosity).
# ---------------------------------------------------------------------------

HELP_A_ROOT = """\
tq - file-based ticket tracker
commands:
  create     create a ticket
  describe   set description
  retitle    set title
  set-type   set type
  set-prio   set priority
  set-parent set parent
  tag        add a tag
  untag      remove a tag
  add-dep    add a dependency
  rm-dep     remove a dependency
  add-note   append a note
  ls         list tickets
  rm         remove ticket
"""

HELP_A_CREATE = """\
tq create TITLE [-d DESC] [-t TYPE] [-p PRIO] [--parent ID] [--tag TAG]... [--dep ID]...
"""
HELP_A_DESCRIBE = "tq describe ID DESC\n"
HELP_A_TAG = "tq tag ID TAG\n"
HELP_A_ADDNOTE = "tq add-note ID NOTE\n"
HELP_A_ADDDEP = "tq add-dep ID DEP_ID\n"
HELP_A_SETPRIO = "tq set-prio ID PRIO\n"
HELP_A_SETPARENT = "tq set-parent ID PARENT_ID\n"

HELP_B_ROOT = """\
tq - file-based ticket tracker
commands:
  create  create a ticket
  edit    modify a ticket
  tag     add a tag (alias)
  add-note append a note (alias)
  ls      list tickets
  rm      remove ticket
"""
HELP_B_CREATE = """\
tq create TITLE [-d DESC] [-t TYPE] [-p PRIO] [--parent ID]
                [--tag TAG]... [--dep ID]... [--note NOTE]...
"""
HELP_B_EDIT = """\
tq edit ID [-d DESC] [-T TITLE] [-t TYPE] [-p PRIO] [--parent ID]
           [--tag TAG]... [--untag TAG]... [--dep ID]... [--rm-dep ID]...
           [--note NOTE]...
"""
HELP_B_TAG = "tq tag ID TAG\n"
HELP_B_ADDNOTE = "tq add-note ID NOTE\n"

HELP_C_ROOT = """\
tq - file-based ticket tracker
commands:
  new   create a ticket (returns id)
  edit  modify a ticket
  ls    list tickets
  rm    remove ticket
"""
HELP_C_NEW = "tq new TITLE   # prints id\n"
HELP_C_EDIT = """\
tq edit ID [-d DESC] [-T TITLE] [-t TYPE] [-p PRIO] [--parent ID]
           [--tag TAG]... [--untag TAG]... [--dep ID]... [--rm-dep ID]...
           [--note NOTE]...
"""

HELP_D_ROOT = """\
tq - file-based ticket tracker
usage: tq <id|new> [flags]
  new                       create a ticket (use with -T to set title)
  <id>                      modify ticket
flags:
  -T TITLE   -d DESC   -t TYPE   -p PRIO   --parent ID
  --tag TAG  --untag TAG  --dep ID  --rm-dep ID  --note NOTE
  ls         list tickets
  rm ID      remove ticket
"""


# ---------------------------------------------------------------------------
# Tasks: a fixed semantic specification, realised as command sequences per
# design. Hand-authored to be the most efficient sensible agent invocation.
# `read` is what stdout would print back (ids, confirmations).
# ---------------------------------------------------------------------------


@dataclass
class Run:
    learn: str
    emit: str
    read: str


# T1: light create -- title + desc + type
T1_LEARN = {
    "A": HELP_A_ROOT + HELP_A_CREATE,
    "B": HELP_B_ROOT + HELP_B_CREATE,
    "C": HELP_C_ROOT + HELP_C_NEW + HELP_C_EDIT,
    "D": HELP_D_ROOT,
}
T1_EMIT = {
    "A": "tq create 'Fix parser dropping trailing commas' -d 'JSON5 inputs raise in parser.py:142' -t bug\n",
    "B": "tq create 'Fix parser dropping trailing commas' -d 'JSON5 inputs raise in parser.py:142' -t bug\n",
    "C": "tq edit $(tq new 'Fix parser dropping trailing commas') -d 'JSON5 inputs raise in parser.py:142' -t bug\n",
    "D": "tq new -T 'Fix parser dropping trailing commas' -d 'JSON5 inputs raise in parser.py:142' -t bug\n",
}
T1_READ = {k: "abf1\n" for k in "ABCD"}
# Design C reads the id twice via command substitution; model that as one print.
T1_READ["C"] = "abf1\n"


# T2: heavy create -- title + desc + type + prio + parent + 2 tags + 1 dep + 1 note
T2_LEARN = {
    "A": HELP_A_ROOT + HELP_A_CREATE + HELP_A_TAG + HELP_A_ADDDEP + HELP_A_ADDNOTE + HELP_A_SETPRIO + HELP_A_SETPARENT,
    "B": HELP_B_ROOT + HELP_B_CREATE,
    "C": HELP_C_ROOT + HELP_C_NEW + HELP_C_EDIT,
    "D": HELP_D_ROOT,
}
# Design A: create takes most flags, but note must be a separate add-note.
T2_EMIT = {
    "A": (
        "tq create 'Add retry to GCS uploads' -d 'transient ServiceUnavailable drops docs' "
        "-t feature -p 2 --parent 9zk2 --tag backend --tag reliability --dep 4mn8\n"
        "tq add-note abf1 'plan rollout carefully'\n"
    ),
    "B": (
        "tq create 'Add retry to GCS uploads' -d 'transient ServiceUnavailable drops docs' "
        "-t feature -p 2 --parent 9zk2 --tag backend --tag reliability --dep 4mn8 "
        "--note 'plan rollout carefully'\n"
    ),
    "C": (
        "tq edit $(tq new 'Add retry to GCS uploads') -d 'transient ServiceUnavailable drops docs' "
        "-t feature -p 2 --parent 9zk2 --tag backend --tag reliability --dep 4mn8 "
        "--note 'plan rollout carefully'\n"
    ),
    "D": (
        "tq new -T 'Add retry to GCS uploads' -d 'transient ServiceUnavailable drops docs' "
        "-t feature -p 2 --parent 9zk2 --tag backend --tag reliability --dep 4mn8 "
        "--note 'plan rollout carefully'\n"
    ),
}
T2_READ = {"A": "abf1\nok\n", "B": "abf1\n", "C": "abf1\n", "D": "abf1\n"}


# T3: mutate -- existing ticket abf1: add tag 'urgent', set prio 1, append note.
T3_LEARN = {
    "A": HELP_A_ROOT + HELP_A_TAG + HELP_A_SETPRIO + HELP_A_ADDNOTE,
    "B": HELP_B_ROOT + HELP_B_EDIT,
    "C": HELP_C_ROOT + HELP_C_EDIT,
    "D": HELP_D_ROOT,
}
T3_EMIT = {
    "A": "tq tag abf1 urgent\ntq set-prio abf1 1\ntq add-note abf1 'customer escalation'\n",
    "B": "tq edit abf1 --tag urgent -p 1 --note 'customer escalation'\n",
    "C": "tq edit abf1 --tag urgent -p 1 --note 'customer escalation'\n",
    "D": "tq abf1 --tag urgent -p 1 --note 'customer escalation'\n",
}
T3_READ = {"A": "ok\nok\nok\n", "B": "ok\n", "C": "ok\n", "D": "ok\n"}


# T4: batch -- create 3 tickets; #2 and #3 are children of #1; #3 depends on #2.
T4_LEARN = {
    "A": HELP_A_ROOT + HELP_A_CREATE + HELP_A_ADDDEP + HELP_A_SETPARENT,
    "B": HELP_B_ROOT + HELP_B_CREATE,
    "C": HELP_C_ROOT + HELP_C_NEW + HELP_C_EDIT,
    "D": HELP_D_ROOT,
}
T4_EMIT = {
    "A": (
        "tq create 'Migrate to async GCS client' -t epic\n"
        "tq create 'Wrap upload in retry' -t task --parent abf1\n"
        "tq create 'Add chaos test for transient failures' -t task --parent abf1 --dep abf2\n"
    ),
    "B": (
        "tq create 'Migrate to async GCS client' -t epic\n"
        "tq create 'Wrap upload in retry' -t task --parent abf1\n"
        "tq create 'Add chaos test for transient failures' -t task --parent abf1 --dep abf2\n"
    ),
    "C": (
        "P=$(tq new 'Migrate to async GCS client'); tq edit $P -t epic\n"
        "C1=$(tq new 'Wrap upload in retry'); tq edit $C1 -t task --parent $P\n"
        "C2=$(tq new 'Add chaos test for transient failures'); tq edit $C2 -t task --parent $P --dep $C1\n"
    ),
    "D": (
        "tq new -T 'Migrate to async GCS client' -t epic\n"
        "tq new -T 'Wrap upload in retry' -t task --parent abf1\n"
        "tq new -T 'Add chaos test for transient failures' -t task --parent abf1 --dep abf2\n"
    ),
}
T4_READ = {k: "abf1\nabf2\nabf3\n" for k in "ABD"}
T4_READ["C"] = "abf1\nok\nabf2\nok\nabf3\nok\n"


# T5: trivial -- add a single tag to existing ticket. Design C's worst case.
T5_LEARN = {
    "A": HELP_A_ROOT + HELP_A_TAG,
    "B": HELP_B_ROOT + HELP_B_TAG,  # alias kept
    "C": HELP_C_ROOT + HELP_C_EDIT,
    "D": HELP_D_ROOT,
}
T5_EMIT = {
    "A": "tq tag abf1 backend\n",
    "B": "tq tag abf1 backend\n",
    "C": "tq edit abf1 --tag backend\n",
    "D": "tq abf1 --tag backend\n",
}
T5_READ = {k: "ok\n" for k in "ABCD"}


TASKS: dict[str, dict[str, Run]] = {}
for tname, learn, emit, read in [
    ("T1 light-create", T1_LEARN, T1_EMIT, T1_READ),
    ("T2 heavy-create", T2_LEARN, T2_EMIT, T2_READ),
    ("T3 mutate", T3_LEARN, T3_EMIT, T3_READ),
    ("T4 batch", T4_LEARN, T4_EMIT, T4_READ),
    ("T5 trivial", T5_LEARN, T5_EMIT, T5_READ),
]:
    TASKS[tname] = {d: Run(learn=learn[d], emit=emit[d], read=read[d]) for d in "ABCD"}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

DESIGNS = ["A", "B", "C", "D"]
DESIGN_NAMES = {
    "A": "status-quo",
    "B": "symmetric",
    "C": "minimal",
    "D": "mega",
}


def fmt_row(cells: list[str], widths: list[int]) -> str:
    return "  ".join(c.ljust(w) for c, w in zip(cells, widths))


def main() -> None:
    # Per-task table
    print("\n=== per-task tokens (emit + read) ===\n")
    header = ["task", "design", "learn", "emit", "read", "per-task"]
    widths = [18, 12, 6, 6, 6, 9]
    print(fmt_row(header, widths))
    print(fmt_row(["-" * w for w in widths], widths))

    per_task: dict[tuple[str, str], tuple[int, int, int]] = {}
    for tname, runs in TASKS.items():
        for d in DESIGNS:
            r = runs[d]
            le, em, rd = n_tok(r.learn), n_tok(r.emit), n_tok(r.read)
            per_task[(tname, d)] = (le, em, rd)
            print(
                fmt_row(
                    [tname, f"{d} {DESIGN_NAMES[d]}", str(le), str(em), str(rd), str(em + rd)],
                    widths,
                )
            )
        print()

    # Lifetime cost: learn paid once (max across tasks, since you read help
    # for the broadest task you tackle in a session), then per-task cost summed.
    print("=== lifetime cost: learn-once + N * mean(per-task) ===\n")
    print(fmt_row(["design", "learn(max)", "mean/task", "N=1", "N=5", "N=20"], [12, 11, 10, 7, 7, 7]))
    print(fmt_row(["-" * 12, "-" * 11, "-" * 10, "-" * 7, "-" * 7, "-" * 7], [12, 11, 10, 7, 7, 7]))
    for d in DESIGNS:
        learns = [per_task[(t, d)][0] for t in TASKS]
        per = [per_task[(t, d)][1] + per_task[(t, d)][2] for t in TASKS]
        learn_max = max(learns)
        mean_per = sum(per) // len(per)
        row = [
            f"{d} {DESIGN_NAMES[d]}",
            str(learn_max),
            str(mean_per),
            str(learn_max + 1 * mean_per),
            str(learn_max + 5 * mean_per),
            str(learn_max + 20 * mean_per),
        ]
        print(fmt_row(row, [12, 11, 10, 7, 7, 7]))

    # Same view but with learn=0 (agents that pattern-match instead of reading help)
    print("\n=== lifetime cost: learn=0 (agent skips help) ===\n")
    print(fmt_row(["design", "mean/task", "N=1", "N=5", "N=20"], [12, 10, 7, 7, 7]))
    print(fmt_row(["-" * 12, "-" * 10, "-" * 7, "-" * 7, "-" * 7], [12, 10, 7, 7, 7]))
    for d in DESIGNS:
        per = [per_task[(t, d)][1] + per_task[(t, d)][2] for t in TASKS]
        mean_per = sum(per) // len(per)
        print(
            fmt_row(
                [f"{d} {DESIGN_NAMES[d]}", str(mean_per), str(mean_per), str(5 * mean_per), str(20 * mean_per)],
                [12, 10, 7, 7, 7],
            )
        )

    print("\ntokenizer: o200k_base")


if __name__ == "__main__":
    main()
