from datetime import datetime, timedelta
from unittest import TestCase

import requests


class AcceptanceTest(TestCase):
    def test_yesterday_report_should_be_available(self):
        now_utc = datetime.utcnow()
        dates_to_check = []
        yesterday = (now_utc.date() - timedelta(days=2)).isoformat()
        dates_to_check.append(yesterday)
        if now_utc.hour >= 1:
            dates_to_check.append((now_utc.date() - timedelta(days=1)).isoformat())
        listing_file = "https://f001.backblazeb2.com/file/mpk-wroclaw/listing.json"
        b2_response = requests.get(listing_file)
        self.assertTrue(b2_response.ok)

        file_listing = b2_response.json()
        file_names = {f["fileName"] for f in file_listing["files"]}
        for date_to_check in dates_to_check:
            self.assertIn(f"{date_to_check}.csv.zip", file_names)

        file_sizes = [int(s["contentLength"]) for s in file_listing["files"]]
        self.assertGreaterEqual(min(file_sizes), 4096)
