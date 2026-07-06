from pathlib import Path

import pytest

from encoding import load_approval_profiles


def test_load_malformed_json_raises_value_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("not valid json\n")

    with pytest.raises(ValueError):
        load_approval_profiles(str(path))

    captured = capsys.readouterr()
    assert "malformed JSON" in captured.out
