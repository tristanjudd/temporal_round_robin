import pytest

from approval_profiles import generate_approval_profiles


@pytest.fixture
def sample_profiles():
    """A small sequence of synthetic approval profiles to round-trip."""
    return list(generate_approval_profiles(4, num_voters=4, num_cands=3))
