from datetime import datetime, timedelta
from unittest import TestCase

import requests


class SmokeTest(TestCase):
    def test_yesterday_report_should_be_available(self):
        now_utc = datetime.utcnow()
        dates_to_check = []
        yesterday = (now_utc.date() - timedelta(days=2)).isoformat()
        dates_to_check.append(yesterday)
        if now_utc.hour >= 1:
            dates_to_check.append((now_utc.date() - timedelta(days=1)).isoformat())
        listing_file = "https://f001.backblazeb2.com/file/mpk-wroclaw/listing.csv"
        b2_response = requests.get(listing_file)
        self.assertTrue(b2_response.ok)

        csv_rows = [l for l in b2_response.content.decode("utf-8").split("\n") if l]
        file_names = {line.partition(";")[0] for line in csv_rows}

        for date_to_check in dates_to_check:
            lookup_file = f"{date_to_check}.csv.zip"
            self.assertIn(lookup_file, file_names, f"There is no {lookup_file} among: {file_names}")

        file_sizes = {int(line.split(";")[2]) for line in csv_rows}
        self.assertGreaterEqual(min(file_sizes), 4096, f"Some files are smaller than 4096 bytes: {file_sizes}")

    def test_website_is_available(self):
        website_url = "https://emkor.github.io/mpyk/"
        b2_response = requests.get(website_url)
        self.assertTrue(b2_response.ok)
        self.assertIsNotNone(b2_response.content)
