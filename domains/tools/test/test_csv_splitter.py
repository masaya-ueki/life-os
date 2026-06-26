"""csv_splitter のスモークテスト。"""

import csv
from pathlib import Path

import pytest

from tools.csv_splitter.split import split_csv


def _write_csv(path: Path, rows: list[list[str]], header: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if header is not None:
            w.writerow(header)
        w.writerows(rows)
    return path


def _read_csv(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


HEADER = ["id", "name", "value"]
ROWS = [["1", "Alice", "100"], ["2", "Bob", "200"], ["3", "Carol", "300"]]


def test_basic_split_with_header(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS, header=HEADER)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=2, has_input_header=True, has_output_header=True)

    assert len(files) == 2
    assert _read_csv(files[0]) == [HEADER] + ROWS[:2]
    assert _read_csv(files[1]) == [HEADER] + ROWS[2:]


def test_exact_multiple(tmp_path: Path) -> None:
    rows = [["1", "a"], ["2", "b"], ["3", "c"], ["4", "d"]]
    src = _write_csv(tmp_path / "input.csv", rows, header=["id", "v"])
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=2)

    assert len(files) == 2


def test_no_input_header(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=2, has_input_header=False, has_output_header=True)

    assert len(files) == 2
    assert _read_csv(files[0]) == ROWS[:2]
    assert _read_csv(files[1]) == ROWS[2:]


def test_no_output_header(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS, header=HEADER)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=2, has_input_header=True, has_output_header=False)

    assert _read_csv(files[0]) == ROWS[:2]


def test_both_headers_false(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=10, has_input_header=False, has_output_header=False)

    assert len(files) == 1
    assert _read_csv(files[0]) == ROWS


def test_single_row_chunk_size_one(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", [["a", "b"]], header=HEADER)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=1)

    assert len(files) == 1


def test_output_dir_auto_created(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS, header=HEADER)
    out_dir = tmp_path / "nested" / "output"

    assert not out_dir.exists()
    split_csv(src, out_dir, chunk_size=10)
    assert out_dir.exists()


def test_file_naming(tmp_path: Path) -> None:
    rows = [[str(i)] for i in range(5)]
    src = _write_csv(tmp_path / "input.csv", rows)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=1, has_input_header=False)

    names = [f.name for f in files]
    assert names == ["part_0000.csv", "part_0001.csv", "part_0002.csv", "part_0003.csv", "part_0004.csv"]


def test_returned_paths_exist(tmp_path: Path) -> None:
    src = _write_csv(tmp_path / "input.csv", ROWS, header=HEADER)
    out_dir = tmp_path / "output"

    files = split_csv(src, out_dir, chunk_size=2)

    for f in files:
        assert f.exists()
