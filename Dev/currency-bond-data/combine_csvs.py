#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine CSV files from a directory after verifying identical columns."
    )
    parser.add_argument(
        "--input-dir",
        default=".",
        help="Directory containing CSV files (default: current directory).",
    )
    parser.add_argument(
        "--output",
        default="combined.csv",
        help="Output CSV file path (default: combined.csv).",
    )
    return parser.parse_args()


def read_header(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            raise ValueError(f"File is empty: {csv_path}")


def combine_csvs(input_dir: Path, output_path: Path) -> None:
    csv_files = sorted(input_dir.glob("*.csv"))
    output_resolved = output_path.resolve()
    csv_files = [p for p in csv_files if p.resolve() != output_resolved]

    if not csv_files:
        raise ValueError(f"No CSV files found in {input_dir}")

    reference_header = read_header(csv_files[0])
    mismatches: list[tuple[Path, list[str]]] = []

    for csv_file in csv_files[1:]:
        header = read_header(csv_file)
        if header != reference_header:
            mismatches.append((csv_file, header))

    if mismatches:
        print("Column mismatch detected. Expected columns from first file:", file=sys.stderr)
        print(f"- {csv_files[0].name}: {reference_header}", file=sys.stderr)
        print("\nFiles with different columns:", file=sys.stderr)
        for file_path, header in mismatches:
            print(f"- {file_path.name}: {header}", file=sys.stderr)
        raise ValueError("Cannot combine CSVs with differing columns.")

    rows_written = 0
    with output_path.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=reference_header)
        writer.writeheader()

        for csv_file in csv_files:
            with csv_file.open("r", encoding="utf-8-sig", newline="") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    writer.writerow(row)
                    rows_written += 1

    print(
        f"Combined {len(csv_files)} files into {output_path} with {rows_written} total rows."
    )


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = input_dir / output_path

    try:
        combine_csvs(input_dir, output_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())