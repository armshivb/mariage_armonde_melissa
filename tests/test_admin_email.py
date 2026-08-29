import unittest

from database import SessionLocal
from models import Guest
from main import add_guest


class AdminGuestEmailTest(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.db.query(Guest).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(Guest).delete()
        self.db.commit()
        self.db.close()

    def test_add_guest_stores_email(self):
        response = add_guest(
            prenom="Alice",
            nom="Martin",
            telephone="0123456789",
            email="alice@example.com",
            db=self.db,
        )

        self.assertEqual(response.status_code, 302)
        guest = self.db.query(Guest).filter_by(prenom="Alice", nom="Martin").first()
        self.assertIsNotNone(guest)
        self.assertEqual(guest.email, "alice@example.com")

    def test_resend_confirmation_email_for_existing_guest(self):
        guest = Guest(
            prenom="Bob",
            nom="Lefevre",
            telephone="0987654321",
            email="bob@example.com",
            code="ABC123",
            response="yes",
            plus_one=1,
        )
        self.db.add(guest)
        self.db.commit()

        # helper should not crash and should keep the same email
        from main import resend_guest_email

        result = resend_guest_email(self.db, guest.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "bob@example.com")


if __name__ == "__main__":
    unittest.main()
