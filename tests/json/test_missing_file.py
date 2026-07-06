import pytest

from encoding import load_approval_profiles


def test_load_missing_file_raises_file_not_found(tmp_path, capsys):
    missing_path = tmp_path / "does_not_exist.jsonl"

    with pytest.raises(FileNotFoundError):
        load_approval_profiles(str(missing_path))

    captured = capsys.readouterr()
    assert str(missing_path) in captured.out
