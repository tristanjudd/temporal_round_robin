# Serial dictator (round-robin) voting rule
#
# Operates on ApprovalProfile objects produced by Lackner's
# perpetual/profiles.py (e.g. uniformly_random_profile or
# approvalprofile_from_2d_euclidean), one round at a time, in the same
# style as the per-round rules in perpetual/perpetual_rules.py.

import random
from typing import Any, Iterable, List, Protocol


class ApprovalProfileLike(Protocol):
    """Structural type for the round profile SerialDictator needs:
    anything exposing `.approval_sets` (this rule never looks at
    `.cands`), regardless of which ApprovalProfile implementation
    produced it."""
    approval_sets: dict


class SerialDictator:
    """Serial dictator rule: a fixed permutation of voters that
    dictates, in turn, one round at a time.

    An instance is callable: each call takes the ApprovalProfile for
    the current round and returns the winner chosen by whichever voter
    is up next in the permutation. The permutation and the position
    within it (whose turn is next) are encapsulated in the instance,
    so callers don't need to track or thread any state themselves.
    """

    def __init__(self, permutation: Iterable[Any]) -> None:
        self.permutation = permutation

    @property
    def permutation(self) -> List[Any]:
        """The fixed voter permutation, in order."""
        return self._permutation

    @permutation.setter
    def permutation(self, value: Iterable[Any]) -> None:
        self._permutation = list(value)
        self._counter = 0

    @property
    def next_voter(self) -> Any:
        """The voter who will be dictator on the next call."""
        return self._permutation[self._counter % len(self._permutation)]

    def __call__(self, profile: ApprovalProfileLike) -> Any:
        """Select this round's winner and advance to the next voter.

        The winner is chosen uniformly at random from the current
        dictator's approval set.

        Parameters
        ----------
        profile : profiles.ApprovalProfile
            The approval profile for the current round.

        Returns
        -------
        winner
            The candidate chosen by this round's dictator.
        """
        dictator = self.next_voter
        winner = random.choice(list(profile.approval_sets[dictator]))
        self._counter += 1
        return winner
