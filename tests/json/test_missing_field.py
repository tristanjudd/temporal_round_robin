import json
from pathlib import Path

import pytest

from encoding import load_approval_profiles


def test_load_missing_field_raises_value_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "missing_field.jsonl"
    record = {"round": 0, "voters": [0, 1], "cands": [0, 1]}
    path.write_text(json.dumps(record) + "\n")

    with pytest.raises(ValueError):
        load_approval_profiles(str(path))

    captured = capsys.readouterr()
    assert "approval_sets" in captured.out
