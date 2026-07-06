# Generates a synthetic election, runs the serial dictator rule over
# it, and persists both the approval-profile history and the
# resulting decision sequence to /experiments/ as JSONL, using the
# existing generation/rule/encoding modules. Runnable as a script or
# importable as a module (run_experiment).

import argparse
import os
from datetime import datetime
from typing import List, Tuple

from approval_profiles import ApprovalProfile, generate_approval_profiles
from display import print_serial_dictator_outcome
from encoding import save_approval_profiles, save_decision_sequence
from serial_dictator import SerialDictator

EXPERIMENTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "experiments")


def run_experiment(
    T: int,
    n: int,
    m: int,
    output_dir: str = EXPERIMENTS_DIR,
    verbose: bool = False,
) -> Tuple[str, str]:
    """Generate a synthetic election and run the serial dictator rule
    over it, saving the results as JSONL.

    Generates T rounds of synthetic approval data for n voters and m
    candidates (approval_profiles.generate_approval_profiles), runs
    SerialDictator over the resulting history, and saves both the
    approval-profile history and the decision sequence to separate
    JSONL files in output_dir (created if it doesn't already exist).

    Parameters
    ----------
    T : int
        Number of rounds to generate and run.
    n : int
        Number of voters.
    m : int
        Number of candidates.
    output_dir : str
        Directory to save the two JSONL files in. Defaults to an
        experiments/ directory next to this module.
    verbose : bool
        If True, print the approval-profile table and outcome
        sequence to the terminal via
        display.print_serial_dictator_outcome.

    Returns
    -------
    tuple of str
        Paths to the saved (approval profiles, decision sequence)
        JSONL files.
    """
    os.makedirs(output_dir, exist_ok=True)

    profiles: List[ApprovalProfile] = list(
        generate_approval_profiles(T, num_voters=n, num_cands=m))

    dictator = SerialDictator(range(n))
    outcome = [dictator(profile) for profile in profiles]

    if verbose:
        print_serial_dictator_outcome(
            profiles, outcome, permutation=dictator.permutation)
        print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"T{T}_n{n}_m{m}_{timestamp}"
    profiles_path = os.path.join(output_dir, f"profiles_{run_name}.jsonl")
    outcome_path = os.path.join(output_dir, f"outcome_{run_name}.jsonl")

    save_approval_profiles(profiles, profiles_path)
    save_decision_sequence(outcome, outcome_path)

    return profiles_path, outcome_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic approval data, run the serial "
                    "dictator rule over it, and save the results as "
                    "JSONL files in /experiments/.")
    parser.add_argument("T", type=int, help="number of rounds")
    parser.add_argument("n", type=int, help="number of voters")
    parser.add_argument("m", type=int, help="number of candidates")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="print the approval profiles and outcome to the terminal")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    profiles_path, outcome_path = run_experiment(
        args.T, args.n, args.m, verbose=args.verbose)
    print(f"Approval profiles saved to '{profiles_path}'.")
    print(f"Decision sequence saved to '{outcome_path}'.")


if __name__ == "__main__":
    main()
