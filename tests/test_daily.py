import io
import json
from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
import unittest
import urllib.error

import daily


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.quotes = daily.load_quotes()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / "state.json"
        self.day = date(2026, 9, 20)

    def test_beijing_date_boundary(self):
        utc = datetime(2026, 9, 19, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(utc.astimezone(daily.BEIJING).date(), self.day)

    def test_full_rotation_without_duplicates(self):
        from datetime import timedelta
        ids = [daily.select_quote(self.quotes, self.day + timedelta(days=i))["id"]
               for i in range(len(self.quotes))]
        self.assertEqual(len(set(ids)), len(self.quotes))
        self.assertEqual(daily.select_quote(self.quotes, self.day + timedelta(days=len(ids)))["id"], ids[0])

    def test_accepted_is_not_resent(self):
        calls = []
        def server(request, timeout):
            calls.append(json.loads(request.data))
            return io.BytesIO(b'{"code":200,"data":"receipt123"}')
        for _ in range(2):
            self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, server), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["channel"], "wechat")
        self.assertEqual(calls[0]["template"], "txt")
        self.assertIn("交易心态应用（非原文）", calls[0]["content"])
        self.assertNotIn("<blockquote>", calls[0]["content"])
        self.assertNotIn("secret", self.state.read_text())
        self.assertEqual(json.loads(self.state.read_text())[str(self.day)]["status"], "accepted")

    def test_rejection_can_be_retried(self):
        def rejected(*args, **kwargs):
            return io.BytesIO(b'{"code":600,"msg":"token secret invalid"}')
        self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, rejected), 1)
        self.assertEqual(json.loads(self.state.read_text())[str(self.day)]["status"], "rejected")
        self.assertNotIn("secret", self.state.read_text())
        def accepted(*args, **kwargs):
            return io.BytesIO(b'{"code":200,"data":"ok123"}')
        self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, accepted), 0)

    def test_timeout_is_not_blindly_retried(self):
        def timeout(*args, **kwargs):
            raise urllib.error.URLError("secret-containing-url")
        self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, timeout), 1)
        self.assertEqual(json.loads(self.state.read_text())[str(self.day)]["status"], "unknown")
        def never(*args, **kwargs):
            self.fail("Uncertain submissions must not be resent")
        self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, never), 0)

    def test_unexpected_response_is_uncertain(self):
        def invalid(*args, **kwargs):
            return io.BytesIO(b'[]')
        self.assertEqual(daily.send_once(self.quotes[0], self.day, "secret", self.state, invalid), 1)
        self.assertEqual(json.loads(self.state.read_text())[str(self.day)]["status"], "unknown")

    def test_html_escaping(self):
        q = dict(self.quotes[0], quote="<script>alert(1)</script>")
        self.assertNotIn("<script>", daily.render(q, self.day))

    def test_trading_scope_and_text_sources(self):
        for q in self.quotes:
            self.assertEqual(q['scope'], '交易心态')
            self.assertTrue(q['theme'])
            text = daily.render_text(q, self.day)
            self.assertIn(q['source'], text)
            self.assertIn(q['quote'], text)
            self.assertIn('交易心态应用（非原文）', text)


if __name__ == "__main__":
    unittest.main()
