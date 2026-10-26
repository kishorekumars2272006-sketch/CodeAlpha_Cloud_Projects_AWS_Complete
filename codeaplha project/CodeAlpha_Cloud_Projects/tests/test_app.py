import os
import tempfile
import unittest
from datetime import date, timedelta

# Use a fresh temporary SQLite database for tests.
fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = "sqlite:///" + db_path
os.environ["SECRET_KEY"] = "test-secret"
from app import app, db, DataRecord, BusPass, record_fingerprint

class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()

    def test_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CodeAlpha Cloud Projects", response.data)

    def test_unique_record_is_saved(self):
        response = self.client.post("/redundancy", data={
            "name": "Priya Kumar", "email": "priya@example.com", "category": "Student"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(DataRecord.query.count(), 1)

    def test_duplicate_record_is_rejected_even_with_case_spaces(self):
        self.client.post("/redundancy", data={
            "name": "Priya Kumar", "email": "priya@example.com", "category": "Student"
        })
        response = self.client.post("/redundancy", data={
            "name": "  PRIYA   KUMAR ", "email": "PRIYA@example.com", "category": " student "
        }, follow_redirects=True)
        self.assertIn(b"Duplicate detected", response.data)
        with app.app_context():
            self.assertEqual(DataRecord.query.count(), 1)

    def test_invalid_email_rejected(self):
        self.client.post("/redundancy", data={
            "name": "A", "email": "not-an-email", "category": "Student"
        })
        with app.app_context():
            self.assertEqual(DataRecord.query.count(), 0)

    def test_bus_booking_uses_server_price(self):
        response = self.client.post("/bus-pass", data={
            "passenger_name": "Test Rider", "email": "rider@example.com",
            "route": "Chennai Central - Tambaram", "pass_type": "single",
            "travel_date": (date.today() + timedelta(days=1)).isoformat(),
            "price": "1"
        }, follow_redirects=True)
        self.assertIn(b"Booking confirmed", response.data)
        with app.app_context():
            booking = BusPass.query.one()
            self.assertEqual(booking.price_paise, 2500)
            self.assertTrue(booking.booking_code.startswith("CA-"))

    def test_past_travel_date_rejected(self):
        response = self.client.post("/bus-pass", data={
            "passenger_name": "Test Rider", "email": "rider@example.com",
            "route": "Chennai Central - Tambaram", "pass_type": "single",
            "travel_date": "2000-01-01"
        }, follow_redirects=True)
        self.assertIn(b"Travel date cannot be in the past", response.data)
        with app.app_context():
            self.assertEqual(BusPass.query.count(), 0)

    def test_health_endpoint(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(db_path)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main(verbosity=2)
