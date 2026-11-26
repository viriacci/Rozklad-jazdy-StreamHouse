import datetime as dt
import sys
import unittest
sys.path.insert(0, "scripts")
from main import week_range, fingerprint

class CalendarTests(unittest.TestCase):
    def test_sunday(self):
        self.assertEqual(week_range(dt.date(2026, 11, 29))[0], dt.date(2026, 11, 30))
    def test_monday(self):
        self.assertEqual(week_range(dt.date(2026, 11, 30))[0], dt.date(2026, 11, 30))
    def test_fingerprint(self):
        dates = week_range(dt.date(2026, 11, 30))
        day = dates[0].isoformat()
        self.assertEqual(fingerprint({day:["Shiroe","ViviOnyx"]}, dates), fingerprint({day:["ViviOnyx","Shiroe","Shiroe"]}, dates))
