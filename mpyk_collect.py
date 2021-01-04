#!/usr/bin/env python

import csv
import os
import signal
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from os import path
from threading import RLock
from time import sleep
from typing import List, Callable
from zipfile import ZipFile

from b2sdk.bucket import Bucket
from b2sdk.v0 import InMemoryAccountInfo, B2Api
from mpyk import *

BUFFER_SIZE = 1000
ARCHIVE_EACH_SEC = 60


class MpykArchiver:
    def __init__(self, executor: ThreadPoolExecutor, csv_dir: str, tmp_zip_dir: str,
                 b2_bucket_factory: Callable[[], Bucket], upload=True):
        self.executor = executor
        self.csv_dir = csv_dir
        self.tmp_zip_dir = tmp_zip_dir
        self.b2_bucket_factory = b2_bucket_factory
        self.upload = upload
        if self.upload:
            print("Logging into Backblaze B2...")
            _ = self.b2_bucket_factory()

    def archive(self, file_name: str) -> None:
        csv_file = path.join(self.csv_dir, file_name)
        zip_file = path.join(self.tmp_zip_dir, f"{file_name}.zip")
        self.executor.submit(self._zip_and_upload, csv_file, zip_file)

    def _zip_and_upload(self, csv_file_path: str, zip_file_path: str):
        with ZipFile(zip_file_path, 'w') as tmp_zip:
            tmp_zip.write(csv_file_path)
        if self.upload:
            bucket = self.b2_bucket_factory()
            bucket.upload_local_file(zip_file_path, file_name=path.basename(csv_file_path))
            os.remove(csv_file_path)
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
                self.archiver.archive(f"{self._last_chunk_date.isoformat()}.csv")
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
        with open(file_path, "a+") as out_f:
            csv_writer = csv.writer(out_f)
            csv_writer.writerows((trans_loc.as_values() for trans_loc in positions))


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
            positions = self.client.get_all_positions()
            self.store.add(positions)
            sleep(each_sec)

    def stop(self) -> None:
        self._running = False


def get_b2_bucket(app_key_id: str, app_key: str, bucket: str) -> Bucket:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", app_key_id, app_key)
    return b2_api.get_bucket_by_name(bucket)


if __name__ == '__main__':
    args = sys.argv[1:]
    each_sec, csv_dir, tmp_zip_dir = int(args[0]), args[1], args[2]

    assert each_sec > 0, f"Given each_sec value ({each_sec}) is <= 0"
    assert path.isdir(csv_dir), f"Given ({csv_dir}) does not exist"
    assert path.isdir(tmp_zip_dir), f"Given ZIP temporary dir ({tmp_zip_dir}) does not exist"

    app_key_id = os.getenv('B2_APP_KEY_ID')
    app_key = os.getenv('B2_APP_KEY')
    bucket_name = os.getenv('B2_BUCKET_NAME')

    assert app_key_id, f"Missing B2_APP_KEY_ID env var"
    assert app_key, f"Missing B2_APP_KEY env var"
    assert bucket_name, f"Missing B2_BUCKET_NAME env var"

    executor = ThreadPoolExecutor(max_workers=os.cpu_count())
    mpyk_client = MpykClient()
    mpyk_archiver = MpykArchiver(executor, csv_dir, tmp_zip_dir,
                                 b2_bucket_factory=lambda: get_b2_bucket(app_key_id, app_key, bucket_name),
                                 upload=True)
    mpyk_store = MpykStore(executor, mpyk_archiver, csv_dir)
    mpyk_collector = MpykCollector(mpyk_client, mpyk_store, each_sec)


    def sig_handler(signum, frame):
        print("Stopping collector due to signal...")
        mpyk_collector.stop()
        print("Flushing buffer...")
        mpyk_store.flush()
        print("Waiting for in-progress tasks")
        executor.shutdown(wait=True)
        print("Stopped successfully!")


    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGABRT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    mpyk_collector.start()
