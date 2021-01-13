#!/usr/bin/env python

import csv
import logging
import os
import signal
import sys
import time
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from os import path
from threading import RLock
from time import sleep
from typing import List, Callable
from zipfile import ZipFile, ZIP_DEFLATED
from zlib import Z_BEST_COMPRESSION

from b2sdk.bucket import Bucket
from b2sdk.v0 import InMemoryAccountInfo, B2Api
from mpyk import *

BUFFER_SIZE = 5000
ARCHIVE_EACH_SEC = 60

log = logging.getLogger("mpyk")


class MpykArchiver:
    def __init__(self, executor: ThreadPoolExecutor, tmp_zip_dir: str,
                 b2_bucket_factory: Callable[[], Bucket], upload=True):
        self.executor = executor
        self.tmp_zip_dir = tmp_zip_dir
        self.b2_bucket_factory = b2_bucket_factory
        self.upload = upload
        if self.upload:
            log.info("Logging into Backblaze B2...")
            _ = self.b2_bucket_factory()

    def archive(self, csv_file_path: str) -> None:
        zip_file = path.join(self.tmp_zip_dir, f"{path.basename(csv_file_path)}.zip")
        self.executor.submit(self._zip_and_upload, csv_file_path, zip_file)

    def _zip_and_upload(self, csv_file_path: str, zip_file_path: str):
        log.info(f"Archiving CSV file at {csv_file_path} into {zip_file_path}")
        csv_file_name = path.basename(csv_file_path)
        zip_file_name = path.basename(zip_file_path)
        start_time = time.time()
        with ZipFile(zip_file_path, 'x', ZIP_DEFLATED, compresslevel=Z_BEST_COMPRESSION) as tmp_zip:
            tmp_zip.write(csv_file_path, arcname=csv_file_name)
        took_s = round(time.time() - start_time, ndigits=3)
        log.info(f"Archiving successful in {took_s}s, removing {csv_file_path}")
        os.remove(csv_file_path)
        if self.upload:
            start_time = time.time()
            log.info(f"Uploading file at {zip_file_path} to BackBlaze cloud as {zip_file_name}")
            bucket = self.b2_bucket_factory()
            bucket.upload_local_file(zip_file_path, file_name=zip_file_name)
            took_s = round(time.time() - start_time, ndigits=3)
            log.info(f"Upload successful in {took_s}s, removing {zip_file_path}")
            os.remove(zip_file_path)


class MpykStore:
    def __init__(self, executor: ThreadPoolExecutor, archiver: MpykArchiver, csv_dir: str,
                 buffer_size: int = BUFFER_SIZE):
        self.executor = executor
        self.archiver = archiver
        self.csv_dir = csv_dir
        self.buffer_size = buffer_size
        self._lock = RLock()
        self._buffer: List[MpykTransLoc] = []
        self._last_chunk_date = datetime.utcnow().date()

    def add(self, positions: List[MpykTransLoc]):
        new_chunk_date = positions[0].timestamp.date()
        with self._lock:
            if new_chunk_date != self._last_chunk_date:
                self.flush()
                self._buffer = positions
                self.archiver.archive(path.join(self.csv_dir, f"{self._last_chunk_date.isoformat()}.csv"))
            elif len(self._buffer) > self.buffer_size:
                self.flush()
                self._buffer = positions
            else:
                self._buffer.extend(positions)
            self._last_chunk_date = new_chunk_date

    def flush(self) -> None:
        with self._lock:
            file_name = path.join(self.csv_dir, f"{self._last_chunk_date.isoformat()}.csv")
            positions = deepcopy(self._buffer)
            self._buffer = []
        self.executor.submit(self._flush, file_name, positions)

    def _flush(self, file_path: str, positions: List[MpykTransLoc]):
        log.debug(f"Flushing buffer with {len(positions)} entries into CSV at {file_path}")
        start_time = time.time()
        with open(file_path, "a+") as out_f:
            csv_writer = csv.writer(out_f)
            csv_writer.writerows((trans_loc.as_values() for trans_loc in positions))
        took_s = round(time.time() - start_time, ndigits=3)
        log.info(f"Done writing {len(positions)} entries in {took_s}s to CSV at {file_path}")


class MpykCollector:
    def __init__(self, client: MpykClient, store: MpykStore, each_sec: int):
        self.client = client
        self.store = store
        self.csv_dir = csv_dir
        self.each_sec = each_sec
        self._running = False

    def start(self) -> None:
        self._running = True
        while self._running:
            log.debug(f"Downloading all tram/bus positions...")
            try:
                positions = self.client.get_all_positions()
                log.debug(f"Storing {len(positions)} positions...")
                self.store.add(positions)
            except ValueError as e:
                log.exception(f"Error on retrieving positions: {e}")
            sleep(each_sec)
        log.info("Collection is disabled, finishing the collector...")

    def stop(self) -> None:
        self._running = False


def get_b2_bucket(app_key_id: str, app_key: str, bucket: str) -> Bucket:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", app_key_id, app_key)
    return b2_api.get_bucket_by_name(bucket)


def setup_logger(level: int = logging.INFO) -> None:
    logging.basicConfig(format='%(asctime)s UTC | %(levelname)s | %(message)s', level=level)
    logging.Formatter.converter = time.gmtime


if __name__ == '__main__':
    args = sys.argv[1:]
    each_sec, csv_dir, tmp_zip_dir = int(args[0]), args[1], args[2]

    assert each_sec > 0, f"Given each_sec value ({each_sec}) is <= 0"
    assert each_sec <= 86400, f"Given each_sec value ({each_sec}) is > 86400 (1 day)"
    assert path.isdir(csv_dir), f"Given ({csv_dir}) does not exist"
    assert path.isdir(tmp_zip_dir), f"Given ZIP temporary dir ({tmp_zip_dir}) does not exist"

    app_key_id = os.getenv('B2_APP_KEY_ID')
    app_key = os.getenv('B2_APP_KEY')
    bucket_name = os.getenv('B2_BUCKET_NAME')
    use_b2 = bool(bucket_name)

    setup_logger()

    if use_b2:
        assert app_key_id, f"Missing B2_APP_KEY_ID env var"
        assert app_key, f"Missing B2_APP_KEY env var"
        assert bucket_name, f"Missing B2_BUCKET_NAME env var"
        log.info(f"BackBlaze upload enabled: bucket {bucket_name} key ID {app_key_id} key length {len(app_key)}")
    else:
        log.warning(f"B2_BUCKET_NAME env var is missing, disabling BackBlaze file upload!")

    log.info(f"Starting mpyk collecting data each {each_sec}s into daily CSVs at {csv_dir}")
    executor = ThreadPoolExecutor(max_workers=1)
    mpyk_client = MpykClient()
    mpyk_archiver = MpykArchiver(executor, tmp_zip_dir,
                                 b2_bucket_factory=lambda: get_b2_bucket(app_key_id, app_key, bucket_name),
                                 upload=use_b2)
    mpyk_store = MpykStore(executor, mpyk_archiver, csv_dir)
    mpyk_collector = MpykCollector(mpyk_client, mpyk_store, each_sec)


    def sig_handler(signum, frame):
        log.info(f"Stopping collector due to signal, might take up to {each_sec}s...")
        mpyk_collector.stop()
        log.debug("Flushing buffer...")
        mpyk_store.flush()
        log.debug("Waiting for in-progress tasks...")
        executor.shutdown(wait=True)
        log.debug("Handling signal finished")


    log.debug("Registering exit signals...")
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGABRT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    log.info(f"Collecting data from {mpyk_client.api_url} ...")
    mpyk_collector.start()
