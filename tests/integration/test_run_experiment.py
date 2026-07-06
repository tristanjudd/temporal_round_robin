import os
from pathlib import Path

from encoding import load_approval_profiles, load_decision_sequence
from run_experiment import run_experiment


def test_run_experiment_creates_and_encodes_consistent_output(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "experiments"
    T, n, m = 6, 4, 3

    assert not output_dir.exists()

    profiles_path, outcome_path = run_experiment(
        T, n, m, output_dir=str(output_dir))

    assert output_dir.is_dir()
    assert os.path.isfile(profiles_path)
    assert os.path.isfile(outcome_path)

    profiles = load_approval_profiles(profiles_path)
    outcome = load_decision_sequence(outcome_path)

    assert len(profiles) == T
    assert len(outcome) == T

    # SerialDictator(range(n)) cycles through voters 0..n-1 in order,
    # so the round-t dictator is deterministically t % n; the saved
    # winner for every round must be one of that dictator's approvals.
    for t, (profile, winner) in enumerate(zip(profiles, outcome)):
        dictator = t % n
        assert winner in profile.approval_sets[dictator]
