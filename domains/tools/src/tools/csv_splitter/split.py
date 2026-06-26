"""CSV ファイルを指定行数ごとに分割するスクリプト。

使い方:
    python -m tools.csv_splitter.split --chunk-size 1000
    python -m tools.csv_splitter.split --input /path/to/file.csv --chunk-size 500
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

_DOMAIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_INPUT_DIR = _DOMAIN_ROOT / "data" / "csv_splitter" / "input"
DEFAULT_OUTPUT_BASE = _DOMAIN_ROOT / "data" / "csv_splitter" / "output"


def split_csv(
    input_path: Path,
    output_dir: Path,
    chunk_size: int,
    has_input_header: bool = True,
    has_output_header: bool = True,
) -> list[Path]:
    """CSV ファイルを chunk_size 行ごとに分割して output_dir に書き出す。

    Returns:
        list[Path]: 作成したファイルのパスリスト（part_0000.csv, part_0001.csv, ...）
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header: list[str] | None = next(reader) if has_input_header else None
        rows = list(reader)

    output_files: list[Path] = []
    for i, chunk_start in enumerate(range(0, len(rows), chunk_size)):
        chunk = rows[chunk_start : chunk_start + chunk_size]
        out_path = output_dir / f"part_{i:04d}.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if has_output_header and header is not None:
                writer.writerow(header)
            writer.writerows(chunk)
        output_files.append(out_path)

    return output_files


def _resolve_input(path: Path) -> Path:
    """ファイルパスまたはディレクトリから入力 CSV を特定する。"""
    if path.is_file():
        return path
    if path.is_dir():
        csvs = sorted(path.glob("*.csv"))
        if len(csvs) == 1:
            return csvs[0]
        if len(csvs) == 0:
            raise FileNotFoundError(f"入力ディレクトリに CSV ファイルが見つかりません: {path}")
        raise ValueError(
            f"入力ディレクトリに複数の CSV ファイルがあります。--input でファイルを直接指定してください: {path}"
        )
    raise FileNotFoundError(f"入力パスが存在しません: {path}")


def main() -> int:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_output = DEFAULT_OUTPUT_BASE / timestamp

    parser = argparse.ArgumentParser(
        description="CSV ファイルを指定行数ごとに分割する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"デフォルト入力ディレクトリ: {DEFAULT_INPUT_DIR}\nデフォルト出力ディレクトリ: {DEFAULT_OUTPUT_BASE}/{{yyyymmdd_HHmmss}}/",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="入力 CSV ファイルまたはディレクトリのパス（デフォルト: data/csv_splitter/input/）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="出力先ディレクトリのパス（デフォルト: data/csv_splitter/output/{timestamp}/）",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="1 ファイルあたりの最大行数（デフォルト: 1000）",
    )
    parser.add_argument(
        "--no-input-header",
        action="store_true",
        help="入力 CSV にヘッダー行がない場合に指定する",
    )
    parser.add_argument(
        "--no-output-header",
        action="store_true",
        help="出力 CSV にヘッダー行を付与しない場合に指定する",
    )
    args = parser.parse_args()

    try:
        resolved_input = _resolve_input(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: {e}")
        return 1

    output_files = split_csv(
        input_path=resolved_input,
        output_dir=args.output,
        chunk_size=args.chunk_size,
        has_input_header=not args.no_input_header,
        has_output_header=not args.no_output_header,
    )

    print(f"分割完了: {len(output_files)} ファイルを {args.output} に出力しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
