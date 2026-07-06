# Synthetic approval-profile generation for temporal voting experiments.
#
# Adapted from Martin Lackner's perpetual voting codebase
# (perpetual/profiles.py and perpetual/experiments/experiments.py).
#
# Modifications relative to the original:
#   - collections.Mapping -> collections.abc.Mapping (removed in Python
#     3.10+) and future.utils.iteritems dropped in favor of plain
#     dict.items(), since this is Python-3-only code.
#   - scipy.spatial.distance.euclidean replaced by a small local
#     helper (math.dist) so this module doesn't require scipy just for
#     a 2D distance computation.
#   - the per-simulation loop body in generate_instances() (fixed voter
#     points, freshly drawn candidate points each round, one
#     ApprovalProfile per round) is exposed directly as a generator,
#     generate_approval_profiles(T, ...), instead of being buried
#     inside batched-simulation/pickling code.

import collections.abc
import math
import random
from typing import Any, Collection, Dict, Iterator, List, Mapping, Optional, Tuple, Union


# approval profile
class ApprovalProfile(object):
    def __init__(
        self,
        voters: List[Any],
        cands: List[Any],
        approval_sets: Union[Mapping[Any, Collection[Any]], List[Collection[Any]]],
    ) -> None:
        self.voters = voters
        if isinstance(approval_sets, collections.abc.Mapping):
            self.approval_sets = approval_sets
        elif isinstance(approval_sets, list):
            assert len(approval_sets) == len(voters)
            self.approval_sets = {}
            for i in range(len(voters)):
                self.approval_sets[voters[i]] = approval_sets[i]
        else:
            raise Exception("type of approval_sets neither dict nor list")
        self.cands = cands
        for v, appr in self.approval_sets.items():
            for c in appr:
                if v not in voters:
                    raise Exception(str(v) + " is not a valid voter; "
                                    + "voters are " + str(voters)+".")
                if c not in cands:
                    raise Exception(str(c) + " is not a valid candidate; "
                                    + "candidates are " + str(cands) + ".")

    def __str__(self) -> str:
        return ("Profile with %d votes and %d candidates: "
                % (len(self.voters), len(self.cands))
                + ', '.join(map(str, self.approval_sets.values())))

    def __deepcopy__(self, memodict: Optional[dict] = None) -> "ApprovalProfile":
        if memodict is None:
            memodict = {}
        import copy
        voters = list(self.voters)
        approvals_sets = copy.deepcopy(self.approval_sets)
        cands = list(self.cands)
        return ApprovalProfile(voters, cands, approvals_sets)

    def has_empty_sets(self) -> bool:
        for appr in self.approval_sets.values():
            if len(appr) == 0:
                return True
        return False


def _euclidean(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.dist(p1, p2)


# create approval profile from 2d coordinates (Euclidean distance)
def approvalprofile_from_2d_euclidean(
    voters: List[Any],
    cands: List[Any],
    voter_points: Dict[Any, Tuple[float, float]],
    cand_points: Dict[Any, Tuple[float, float]],
    threshold: float,
) -> ApprovalProfile:
    approval_sets = {}
    for v in voters:
        distances = {c: _euclidean(voter_points[v], cand_points[c])
                     for c in cands}
        mindist = min(distances.values())
        approval_sets[v] = [c for c in cands
                            if distances[c] <= mindist * threshold]
    return ApprovalProfile(voters, cands, approval_sets)


# generate a list of 2d coordinates subject to
# various distributions
def generate_2d_points(
    pointids: List[Any], mode: str, sigma: float
) -> Dict[Any, Tuple[float, float]]:

    numpoints = len(pointids)
    points: List[Tuple[float, float]] = [(0.0, 0.0)] * numpoints

    # normal distribution, 1/3 of points centered on (-0.5,-0.5),
    #                      2/3 of points on (0.5,0.5)
    #                      all within [-1,1]x[-1,1]
    if mode == "eucl1":
        def within_bounds(point: Tuple[float, float]) -> bool:
            return (point[0] <= 1 and point[0] >= -1 and
                    point[1] <= 1 and point[1] >= -1)
        for i in range(int(numpoints // 3)):
            while True:
                points[i] = (random.gauss(-0.5, sigma),
                             random.gauss(-0.5, sigma))
                if within_bounds(points[i]):
                    break
        for i in range(numpoints // 3, numpoints):
            while True:
                points[i] = (random.gauss(0.5, sigma),
                             random.gauss(0.5, sigma))
                if within_bounds(points[i]):
                    break
    # normal distribution, 1/3 of points centered on (-0.5,-0.5),
    #                      2/3 of points on (0.5,0.5)
    elif mode == "eucl2":
        for i in range(int(numpoints // 3)):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(int(numpoints // 3), numpoints):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(0.5, sigma))
    # normal distribution, 1/5 of points centered on (-0.5,-0.5),
    #                      4/5 of points on (0.5,0.5)
    elif mode == "eucl4":
        for i in range(numpoints // 5):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(numpoints // 5, numpoints):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(0.5, sigma))
    # normal distribution, 3/5 of points centered on (-0.25,0),
    #                      2/5 of points on (0.25,0)
    elif mode == "eucl6":
        for i in range(2 * numpoints // 5):
            points[i] = (random.gauss(-0.25, sigma),
                         random.gauss(0, sigma))
        for i in range(2 * numpoints // 5, numpoints):
            points[i] = (random.gauss(0.25, sigma),
                         random.gauss(0, sigma))
    # normal distribution
    elif mode == "normal":
        for i in range(numpoints):
            points[i] = (random.gauss(0., sigma),
                         random.gauss(0., sigma))
    # normal distribution, each 1/4 of points centered on (+-0.5,+-0.5)
    elif mode == "eucl5":
        for i in range(numpoints // 4):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(numpoints // 4, 2 * numpoints // 4):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(0.5, sigma))
        for i in range(2 * numpoints // 4, 3 * numpoints // 4):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(0.5, sigma))
        for i in range(3 * numpoints // 4, numpoints):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(-0.5, sigma))
    # normal distribution, 1/5 of points centered on (-0.5,-0.5),
    #                      1/5 of points centered on (-0.5,0.5),
    #                      1/5 of points centered on (0.5,-0.5),
    #                      2/5 of points on (0.5,0.5)
    elif mode == "eucl3":
        for i in range(numpoints // 5):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(numpoints // 5, 2 * numpoints // 5):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(0.5, sigma))
        for i in range(2 * numpoints // 5, 3 * numpoints // 5):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(3 * numpoints // 5, numpoints):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(0.5, sigma))
    elif mode == "eucl2plus":
        for i in range(numpoints // 6):
            points[i] = (random.gauss(-0.5, sigma),
                         random.gauss(-0.5, sigma))
        for i in range(numpoints // 6, numpoints):
            points[i] = (random.gauss(0.5, sigma),
                         random.gauss(0.5, sigma))
    elif mode == "uniform_square":
        for i in range(numpoints):
            points[i] = (random.uniform(-1, 1),
                         random.uniform(-1, 1))
    else:
        raise ValueError("mode " + str(mode) + " not known")

    pointsdict = {}
    random.shuffle(points)
    for i in range(numpoints):
        pointsdict[pointids[i]] = points[i]

    return pointsdict


# generate T rounds of approval profiles for a single simulation
# instance, following the per-simulation loop body of
# experiments/experiments.py: generate_instances(). Voters are placed
# once (voterpointmode/sigma) and stay fixed across all rounds;
# candidates are (re-)placed anew every round (candpointmode/sigma),
# and each round's ApprovalProfile is derived from the euclidean
# distances between voters and candidates using approval_threshold.
def generate_approval_profiles(
    T: int,
    num_voters: int = 20,
    num_cands: int = 5,
    sigma: float = 0.2,
    voterpointmode: str = "eucl5",
    candpointmode: str = "uniform_square",
    approval_threshold: float = 1.5,
) -> Iterator[ApprovalProfile]:
    """Generate T rounds of synthetic approval profiles.

    Parameters
    ----------
    T : int
        Number of rounds (profiles) to generate.
    num_voters : int
        Number of voters.
    num_cands : int
        Number of candidates.
    sigma : float
        Standard deviation used by the 2d point distributions.
    voterpointmode : str
        Distribution mode for voter points (see generate_2d_points);
        drawn once and kept fixed across all T rounds.
    candpointmode : str
        Distribution mode for candidate points (see
        generate_2d_points); redrawn independently every round.
    approval_threshold : float
        A candidate is approved by a voter if its distance is within
        approval_threshold times the voter's nearest-candidate
        distance.

    Yields
    ------
    ApprovalProfile
        One approval profile per round, T in total.
    """
    voters = list(range(num_voters))
    cands = list(range(num_cands))
    voter_points = generate_2d_points(voters, voterpointmode, sigma)

    for _ in range(T):
        cand_points = generate_2d_points(cands, candpointmode, sigma)
        yield approvalprofile_from_2d_euclidean(
            voters, cands, voter_points, cand_points, approval_threshold)
