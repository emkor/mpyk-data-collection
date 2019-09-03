#!/usr/bin/env python3

import sys
from datetime import datetime
from os import path
from typing import List, Iterator

CHUNK_SIZE_KB = 64
ROW_DELIMITER = "\n"
CELL_DELIMITER = ";"
ENCODING = "utf-8"


def read_rows_in_chunks(file_path: str) -> Iterator[List[List[str]]]:
    buffer_size_bytes = round(CHUNK_SIZE_KB * 1000, ndigits=None)
    cached_last_line = ""
    with open(file_path, "rb") as input_file:
        while True:
            data = input_file.read(buffer_size_bytes)
            if not data:
                break
            try:
                one_line = cached_last_line + data.decode(ENCODING)
                rows = one_line.split(ROW_DELIMITER)
                cached_last_line = rows.pop(-1)  # last line may not be complete up to row delimiter!
                cells_in_rows = [r.split(CELL_DELIMITER) for r in rows]
                yield cells_in_rows
            except Exception as e:
                print("Error on parsing CSV: {}".format(e))
                cached_last_line = ""
                yield []
        # don't forget last cached line
        yield [cached_last_line.split(CELL_DELIMITER)] if cached_last_line else []


def optimize_row(cells: List[str]) -> List[str]:
    optimized_date = datetime.fromisoformat(cells[0]).replace(microsecond=0).isoformat()
    return [optimized_date, cells[1], cells[2], cells[3], cells[4], cells[5]]


def main(in_csv: str, out_csv: str) -> int:
    lines = 0
    with open(out_csv, "wb") as out_csv:
        for in_rows in read_rows_in_chunks(in_csv):
            output_rows = [(";".join(optimize_row(cells)) + "\n").encode("utf-8") for cells in in_rows if cells]
            out_csv.writelines(output_rows)
            lines += len(output_rows)
    return lines


if __name__ == '__main__':
    input_csv = path.abspath(str(sys.argv[1]))
    output_csv = path.abspath(str(sys.argv[2]))
    if path.isfile(output_csv):
        print(f"File {output_csv} already exists, existing")
        exit(1)
    if not path.isfile(input_csv):
        print(f"File {input_csv} does not exist!")
        exit(1)
    print(f"Opening {input_csv}")
    line_count = main(in_csv=input_csv, out_csv=output_csv)
    print(f"Optimized {line_count} CSV rows into {output_csv}!")
    exit(0)
