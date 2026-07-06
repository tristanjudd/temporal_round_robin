# JSON Lines persistence for approval profiles and voting-rule
# outcomes.
#
# Stores/loads the round-by-round output of
# approval_profiles.generate_approval_profiles, and the round-by-round
# decision sequence returned by voting rules such as SerialDictator, as
# JSON Lines: one self-contained JSON object per round, so the file
# can be inspected by eye, streamed/appended to incrementally, and
# parsed by any language without depending on this codebase.

import json

from approval_profiles import ApprovalProfile


def save_approval_profiles(profiles, path):
    """Save a sequence of ApprovalProfile objects to a JSONL file.

    Each round is written as one independent JSON object on its own
    line:
        {"round": t, "voters": [...], "cands": [...],
         "approval_sets": {voter: [approved candidates]}}

    Parameters
    ----------
    profiles : sequence of ApprovalProfile
        One profile per round, e.g. as produced by
        approval_profiles.generate_approval_profiles.
    path : str
        Destination file path.

    Raises
    ------
    OSError
        If the file cannot be opened or written to.
    ValueError
        If a profile's data cannot be represented as JSON.
    """
    num_rounds = 0
    try:
        with open(path, "w") as f:
            for t, profile in enumerate(profiles):
                record = {
                    "round": t,
                    "voters": list(profile.voters),
                    "cands": list(profile.cands),
                    "approval_sets": {
                        str(v): list(profile.approval_sets[v])
                        for v in profile.voters
                    },
                }
                try:
                    line = json.dumps(record)
                except TypeError as e:
                    print(f"Error: round {t} of the profile sequence "
                          f"could not be converted to JSON: {e}")
                    raise ValueError(
                        f"round {t} is not JSON-serializable") from e
                f.write(line + "\n")
                num_rounds += 1
    except OSError as e:
        print(f"Error: could not write approval profiles to '{path}': {e}")
        raise

    print(f"Saved {num_rounds} rounds to '{path}'.")


def load_approval_profiles(path):
    """Load a sequence of ApprovalProfile objects from a JSONL file
    written by save_approval_profiles.

    Parameters
    ----------
    path : str
        Path to the JSONL file to read.

    Returns
    -------
    list of ApprovalProfile
        One profile per round, in the order they were written.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    OSError
        If the file exists but cannot be read.
    ValueError
        If a line is not valid JSON, is missing required fields, or
        cannot be reconstructed into an ApprovalProfile.
    """
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: approval profile file not found: '{path}'")
        raise
    except OSError as e:
        print(f"Error: could not read approval profile file '{path}': {e}")
        raise

    profiles = []
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error: malformed JSON on line {line_number} of "
                  f"'{path}': {e}")
            raise ValueError(
                f"malformed JSON on line {line_number} of '{path}'") from e

        try:
            voters = record["voters"]
            cands = record["cands"]
            raw_approval_sets = record["approval_sets"]
        except KeyError as e:
            print(f"Error: line {line_number} of '{path}' is missing "
                  f"required field {e}")
            raise ValueError(
                f"line {line_number} of '{path}' is missing required "
                f"field {e}") from e

        # JSON object keys are always strings, so voter ids (typically
        # ints) written as dict keys need to be mapped back to their
        # original values using the "voters" list on the same line.
        try:
            voter_by_key = {str(v): v for v in voters}
            approval_sets = {
                voter_by_key[key]: approved
                for key, approved in raw_approval_sets.items()
            }
        except KeyError as e:
            print(f"Error: line {line_number} of '{path}' has an "
                  f"approval_sets entry for voter {e} not present in "
                  f"its 'voters' list")
            raise ValueError(
                f"line {line_number} of '{path}' references unknown "
                f"voter {e}") from e

        try:
            profiles.append(ApprovalProfile(voters, cands, approval_sets))
        except Exception as e:
            print(f"Error: could not reconstruct an approval profile "
                  f"from line {line_number} of '{path}': {e}")
            raise ValueError(
                f"invalid approval profile on line {line_number} of "
                f"'{path}'") from e

    print(f"Loaded {len(profiles)} rounds from '{path}'.")
    return profiles


def save_decision_sequence(outcome, path):
    """Save a decision (outcome) sequence to a JSONL file.

    Each round is written as one independent JSON object on its own
    line: {"round": t, "winner": w}.

    Parameters
    ----------
    outcome : sequence
        The winner selected in each round, e.g. as produced by calling
        a voting rule such as SerialDictator once per round.
    path : str
        Destination file path.

    Raises
    ------
    OSError
        If the file cannot be opened or written to.
    ValueError
        If a winner cannot be represented as JSON.
    """
    num_rounds = 0
    try:
        with open(path, "w") as f:
            for t, winner in enumerate(outcome):
                record = {"round": t, "winner": winner}
                try:
                    line = json.dumps(record)
                except TypeError as e:
                    print(f"Error: round {t} of the decision sequence "
                          f"could not be converted to JSON: {e}")
                    raise ValueError(
                        f"round {t} is not JSON-serializable") from e
                f.write(line + "\n")
                num_rounds += 1
    except OSError as e:
        print(f"Error: could not write decision sequence to '{path}': {e}")
        raise

    print(f"Saved {num_rounds} rounds to '{path}'.")


def load_decision_sequence(path):
    """Load a decision (outcome) sequence from a JSONL file written by
    save_decision_sequence.

    Parameters
    ----------
    path : str
        Path to the JSONL file to read.

    Returns
    -------
    list
        The winner for each round, in the order they were written.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    OSError
        If the file exists but cannot be read.
    ValueError
        If a line is not valid JSON or is missing the winner field.
    """
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: decision sequence file not found: '{path}'")
        raise
    except OSError as e:
        print(f"Error: could not read decision sequence file '{path}': {e}")
        raise

    outcome = []
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error: malformed JSON on line {line_number} of "
                  f"'{path}': {e}")
            raise ValueError(
                f"malformed JSON on line {line_number} of '{path}'") from e

        try:
            outcome.append(record["winner"])
        except KeyError as e:
            print(f"Error: line {line_number} of '{path}' is missing "
                  f"required field {e}")
            raise ValueError(
                f"line {line_number} of '{path}' is missing required "
                f"field {e}") from e

    print(f"Loaded {len(outcome)} rounds from '{path}'.")
    return outcome
