# Real-world approval-profile loading (.tsoi / .ttoi file formats),
# adapted from Martin Lackner's perpetual/file_loader.py.
#
# Produces the same kind of ApprovalProfile history (a list of
# approval_profiles.ApprovalProfile, one per round) as
# approval_profiles.generate_approval_profiles, so real and synthetic
# data are interchangeable everywhere else in this project
# (SerialDictator, encoding, display).
#
# Modifications relative to the original:
#   - builds approval_profiles.ApprovalProfile (this project's own
#     copy) instead of perpetual/profiles.py's ApprovalProfile.
#   - paths are resolved relative to this module's own directory (the
#     project root) rather than perpetual/'s directory, so a `data/`
#     folder is expected as a sibling of this file, e.g.
#     data/eurovision_song_contest_tsoi, following the download
#     instructions in perpetual/README.md.
#   - error messages are raised as plain formatted strings (some of
#     Lackner's original `raise Exception(a, b)` calls relied on
#     Python 2/3 tuple-formatting of exception args).

import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from approval_profiles import ApprovalProfile

script_dir = os.path.dirname(os.path.abspath(__file__))


def load_real_data_profiles(
    dir_name: str,
    threshold: Optional[Union[int, float]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    only_complete: bool = False,
    with_weights: bool = False,
) -> Tuple[List[ApprovalProfile], Set[Any]]:
    """Load all .tsoi/.ttoi files directly within the given directory
    into an ApprovalProfile history, one profile per round (file).

    Files should conform to the naming convention of *_date.tsoi or
    *_date.ttoi, where the date format should be sortable, so that
    sorting file names sorts rounds from oldest to newest.

    Parameters
    ----------
    dir_name : str
        Path to the directory with the files, relative to this
        module's directory (the project root).
    threshold : int or float, optional
        An int for with_weights=False means up to the rank threshold
        (how many top-ranked candidates are approved).
        A float for with_weights=True means at least a weight of
        max_weight * threshold needs to be reached within a ranking.
        None uses the defaults: 0.9 with weights, half the ranking
        length otherwise.
    from_date : str, optional
        Date in the same format as in the filenames. Files before this
        date are ignored.
    to_date : str, optional
        Date in the same format as in the filenames. Files after this
        date are ignored.
    only_complete : bool
        If True, all voters that are not present in every profile are
        removed.
    with_weights : bool
        States if weights are used to decide on the approval set.

    Returns
    -------
    list of ApprovalProfile, set
        The approval profile history (one per round) and the set of
        all voters appearing in it.
    """
    file_dir, files = get_file_names(dir_name)

    profile_history: List[ApprovalProfile] = []
    all_voters: Set[Any] = set()
    if file_dir is not None:
        # sorts from oldest to newest if name is sortable by date
        # (YYYYMMDD)
        files = sorted(files)
        for f in files:
            if f.endswith(".tsoi") or f.endswith(".ttoi"):
                if from_date is not None or to_date is not None:
                    date = f.split("_")[-1].split(".t")[0]
                    if from_date is not None and date < from_date:
                        continue
                    if to_date is not None and date > to_date:
                        break
                candidates, profile = load_file(
                    os.path.join(file_dir, f), threshold, with_weights)
                profile_history.append(ApprovalProfile(
                    list(profile.keys()), candidates, profile))
                all_voters = all_voters.union(list(profile.keys()))
    if only_complete:
        profile_history, all_voters = \
            remove_additional_voters(profile_history, all_voters)
    if len(profile_history) == 0 or len(all_voters) == 0:
        raise Exception(f"No data found in {dir_name}")
    return profile_history, all_voters


def load_file(
    abs_path: str, threshold: Optional[Union[int, float]], with_weights: bool
) -> Tuple[List[int], Dict[str, List[int]]]:
    with open(abs_path, "r") as f:
        lines = f.readlines()
        candidate_count = int(lines[0])
        after_candidates = candidate_count + 1
        profile = {}
        rankings_count = int(lines[after_candidates].split(',')[1])
        last_ranking_line = after_candidates + 1 + rankings_count
        used_candidates = set()
        for line in lines[after_candidates + 1: last_ranking_line + 1]:
            parts = line.split(':')
            if len(parts) != 2:
                print("####### ERROR #######")
                print("ranking Data seems to have wrong format in "
                      "file", abs_path)
                raise Exception(f"Unknown format: {line}")
            local_ranking: List[int] = []
            profile[parts[0]] = local_ranking  # name of the voter
            if with_weights:
                get_ranking_with_weights(parts[1], local_ranking,
                                         threshold)
            else:
                get_ranking_without_weights(parts[1], local_ranking,
                                            threshold)
            for candidate in local_ranking:
                used_candidates.add(candidate)

        return list(used_candidates), profile


def get_ranking_with_weights(
    line: str, appr_set: List[int], threshold: Optional[float]
) -> None:
    if threshold is None:
        threshold = 0.9
    ranking = line.split(',')[1:]
    if len(ranking) == 0:
        return

    max_weight = None
    tied = False
    curr_voters = ""
    for i in range(len(ranking)):
        voter = ranking[i].strip()
        if not tied:
            if voter.startswith("{"):
                tied = True
                curr_voters = voter
                if "}" in voter:
                    raise Exception("Single voter in {} is invalid")
            else:
                if max_weight is None:
                    max_weight = get_weight(voter)
                if get_weight(voter) >= max_weight * threshold:
                    add_candidate(voter, appr_set)
                else:
                    break
        else:
            curr_voters += "," + voter
            if "}" in curr_voters:
                tied = False
                if max_weight is None:
                    max_weight = get_weight(curr_voters)
                if get_weight(curr_voters) >= max_weight * threshold:
                    add_candidate(curr_voters, appr_set)
                    curr_voters = ""
                else:
                    break
            else:
                continue


def get_weight(rank: str) -> float:
    parts = rank.split("[")
    if len(parts) != 2:
        raise Exception("Invalid format for with weights")
    else:
        weight = float(parts[1].split("]")[0])
    return weight


def add_candidate(rank: str, appr_set: List[int]) -> None:
    parts = rank.split("[")
    if 0 < len(parts) < 3:
        candidate = parts[0].strip()
        if candidate.find("{") != -1:
            if candidate[0] != "{" or candidate[-1] != "}":
                raise Exception(
                    f"Invalid format for tied candidates: {rank}")
            candidates = candidate[1:-1].split(",")
            for c in candidates:
                appr_set.append(int(c.strip()))
        else:
            appr_set.append(int(candidate))
    else:
        raise Exception(f"Invalid format: {rank}")


def get_ranking_without_weights(
    line: str, appr_set: List[int], threshold: Optional[float]
) -> None:
    ranking = line.split(',')[1:]
    if threshold is None:
        threshold = max(len(ranking) // 2, 1)

    if len(ranking) == 0:
        return

    tied = False
    curr_voters = ""
    for i in range(len(ranking)):
        if threshold > 0:
            voter = ranking[i].strip()
            if not tied:
                if voter.startswith("{"):
                    tied = True
                    curr_voters = voter
                    if "}" in voter:
                        raise Exception("Single voter in {} is invalid")
                else:
                    add_candidate(voter, appr_set)
                    threshold -= 1
            else:
                curr_voters += "," + voter
                if "}" in voter:
                    add_candidate(curr_voters, appr_set)
                    curr_voters = ""
                    threshold -= 1
                else:
                    continue
        else:
            break


def get_file_names(dir_name: str) -> Tuple[str, List[str]]:
    input_path = os.path.join(script_dir, dir_name)
    files = []
    file_dir = None
    for (dir_path, _, filenames) in os.walk(input_path):
        file_dir = dir_path
        files = filenames
        break
    if file_dir is None or len(files) == 0:
        raise Exception(f"No files found in {input_path}")
    return file_dir, files


def remove_additional_voters(
    profile_history: List[ApprovalProfile], all_voters: Set[Any]
) -> Tuple[List[ApprovalProfile], Set[Any]]:
    """Return a profile history where every round has exactly the same
    voters (the intersection of voters present in all rounds)."""
    voters = set(all_voters)
    for profile in profile_history:
        voters = voters.intersection(profile.voters)
    if len(voters) == len(all_voters):
        return profile_history, all_voters

    voter_list = list(voters)
    restricted_history = []
    for profile in profile_history:
        if len(profile.voters) == len(voters):
            restricted_history.append(profile)
        else:
            appr_set = {}
            cands: Set[Any] = set()
            for voter, appr in profile.approval_sets.items():
                if voter in voters:
                    appr_set[voter] = appr
                    cands = cands.union(appr)
            restricted_history.append(
                ApprovalProfile(voter_list, list(cands), appr_set))
    return restricted_history, voters
