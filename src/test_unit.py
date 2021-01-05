import os
import tempfile
from os import path
from concurrent.futures.thread import ThreadPoolExecutor
from unittest.mock import Mock
from zipfile import ZipFile

from src.mpyk_collect import MpykArchiver

TEST_PREFIX = "mpyk_"


def test_archiver_should_pack_zip():
    executor = ThreadPoolExecutor(max_workers=1)
    with tempfile.TemporaryDirectory(prefix=TEST_PREFIX) as tmp_zip_dir:
        with tempfile.NamedTemporaryFile("w", delete=False, prefix=TEST_PREFIX, suffix=".txt") as tmp_text_file:
            tmp_text_file.write(", ".join((str(n) for n in range(1000))))
        try:
            assert path.isfile(tmp_text_file.name), f"Expected text file at {tmp_text_file.name} is missing"
            txt_file_size = os.stat(tmp_text_file.name).st_size
            assert txt_file_size > 1, f"Expected text file at {tmp_text_file.name} looks empty"

            archiver = MpykArchiver(executor, tmp_zip_dir, Mock(), upload=False)
            archiver.archive(tmp_text_file.name)

            executor.shutdown(wait=True)
            expected_zip_file = path.join(tmp_zip_dir, f"{path.basename(tmp_text_file.name)}.zip")
            assert path.isfile(expected_zip_file), f"Expected ZIP file at {expected_zip_file} is missing"
            zip_file_size = os.stat(expected_zip_file).st_size
            assert zip_file_size > 1, f"Expected ZIP file at {expected_zip_file} looks empty"
            assert zip_file_size < txt_file_size, f"ZIP is larger ({zip_file_size}) than original ({txt_file_size})"

            with ZipFile(expected_zip_file) as zip_file:
                namelist = zip_file.namelist()
                assert path.basename(tmp_text_file.name) in namelist, \
                    f"Expected text file name ({path.basename(tmp_text_file.name)}) not found in ZIP"

        finally:
            try:
                os.remove(tmp_text_file.name)
                os.remove(expected_zip_file)
            finally:
                pass
