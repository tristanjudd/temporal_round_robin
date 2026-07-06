# Terminal reporting utilities for temporal voting experiments.
#
# Kept separate from serial_dictator.py / approval_profiles.py so that
# those modules stay free of any printing/formatting dependencies.

from typing import Any, Iterable, Protocol, Sequence

import pandas as pd


class ApprovalProfileLike(Protocol):
    """Structural type for the profiles this module prints: anything
    exposing `.voters` and `.approval_sets`."""
    voters: Iterable[Any]
    approval_sets: dict


def print_serial_dictator_outcome(
    profiles: Sequence[ApprovalProfileLike],
    outcome: Sequence[Any],
    max_rows: int = 10,
    max_cols: int = 10,
) -> None:
    """Pretty-print a serial dictator run to the terminal.

    Prints a voters-by-rounds table of approval sets, followed by the
    resulting outcome sequence beneath it. Large tables are truncated
    with '...' rows/columns (pandas-style) so the output stays
    readable regardless of the number of voters or rounds.

    Parameters
    ----------
    profiles : sequence of ApprovalProfile
        One approval profile per round, e.g. as produced by
        approval_profiles.generate_approval_profiles.
    outcome : sequence
        The winner selected in each round (same length as profiles),
        e.g. as produced by calling serial_dictator once per round.
    max_rows : int
        Maximum number of voter rows to display before truncating.
    max_cols : int
        Maximum number of round columns to display before truncating.
    """
    profiles = list(profiles)
    outcome = list(outcome)
    if len(profiles) != len(outcome):
        raise ValueError("profiles and outcome must have the same length")

    voters = list(profiles[0].voters)

    table = pd.DataFrame(
        {t: [_format_approvals(profile.approval_sets[v]) for v in voters]
         for t, profile in enumerate(profiles)},
        index=voters,
    )
    table.index.name = "voter"
    table.columns.name = "round"

    print(table.to_string(max_rows=max_rows, max_cols=max_cols))
    print()
    print("outcome:", _format_sequence(outcome, max_cols))


def _format_approvals(approvals: Iterable[Any]) -> str:
    try:
        approvals = sorted(approvals)
    except TypeError:
        approvals = list(approvals)
    return "{" + ",".join(str(c) for c in approvals) + "}"


def _format_sequence(seq: Sequence[Any], max_len: int) -> str:
    if len(seq) <= max_len:
        shown = [str(x) for x in seq]
    else:
        head = max_len // 2
        tail = max_len - head
        shown = ([str(x) for x in seq[:head]] + ["..."]
                 + [str(x) for x in seq[-tail:]])
    return ", ".join(shown)
