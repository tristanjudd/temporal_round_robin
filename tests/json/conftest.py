from typing import List

import pytest

from approval_profiles import ApprovalProfile, generate_approval_profiles


@pytest.fixture
def sample_profiles() -> List[ApprovalProfile]:
    """A small sequence of synthetic approval profiles to round-trip."""
    return list(generate_approval_profiles(4, num_voters=4, num_cands=3))
