from pathlib import Path
from typing import List

from approval_profiles import ApprovalProfile
from encoding import load_approval_profiles, save_approval_profiles


def test_round_trip_preserves_profiles(
    tmp_path: Path, sample_profiles: List[ApprovalProfile]
) -> None:
    path = tmp_path / "profiles.jsonl"

    save_approval_profiles(sample_profiles, str(path))
    loaded = load_approval_profiles(str(path))

    assert len(loaded) == len(sample_profiles)
    for original, restored in zip(sample_profiles, loaded):
        assert restored.voters == original.voters
        assert restored.cands == original.cands
        for v in original.voters:
            assert (sorted(restored.approval_sets[v])
                    == sorted(original.approval_sets[v]))
