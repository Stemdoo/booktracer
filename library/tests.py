from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from .models import Book, BookReservation, ReservationEvent, Author, Genre


class ReservationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="test_user",
            password="test_password"
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            password="test_password"
        )

        self.author = Author.objects.create(name="Тестовый автор")
        self.genre = Genre.objects.create(name="Тестовый жанр")

        self.book = Book.objects.create(
            title="Тестовая книга",
            description="Описание тестовой книги",
            snippet="Фрагмент тестовой книги",
            available_copies=2,
            author=self.author,
            genre=self.genre
        )

        self.client.force_authenticate(user=self.user)

    def create_reservation(self):
        return BookReservation.objects.create(
            user=self.user,
            book=self.book,
            status="created"
        )

    def test_reservation_creation(self):
        reservation = self.create_reservation()

        self.assertEqual(reservation.status, "created")
        self.assertEqual(
            BookReservation.objects.filter(user=self.user).count(),
            1
        )

    def test_initial_event_is_created_by_api(self):
        response = self.client.post(
            "/api/reservations/",
            {"book": self.book.id},
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ReservationEvent.objects.filter(
                event_type="created"
            ).exists()
        )

    def test_user_cannot_view_another_users_reservation(self):
        reservation = BookReservation.objects.create(
            user=self.other_user,
            book=self.book,
            status="created"
        )

        response = self.client.get(
            f"/api/reservations/{reservation.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_confirm_decreases_available_copies(self):
        reservation = self.create_reservation()

        response = self.client.post(
            f"/api/reservations/{reservation.id}/action/",
            {"action": "confirm"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.book.refresh_from_db()
        reservation.refresh_from_db()

        self.assertEqual(reservation.status, "confirmed")
        self.assertEqual(self.book.available_copies, 1)

    def test_invalid_transition_is_rejected(self):
        reservation = self.create_reservation()

        response = self.client.post(
            f"/api/reservations/{reservation.id}/action/",
            {"action": "return"},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(reservation.status, "created")
        self.assertEqual(self.book.available_copies, 2)

    def test_transaction_rollback_on_error(self):
        from unittest.mock import patch

        reservation = self.create_reservation()

        initial_status = reservation.status
        initial_copies = self.book.available_copies
        initial_events = ReservationEvent.objects.filter(
            reservation=reservation
        ).count()

        with patch(
                "library.views.ReservationEvent.objects.create",
                side_effect=RuntimeError("Тестовая ошибка")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    f"/api/reservations/{reservation.id}/action/",
                    {"action": "confirm"},
                    format="json",
                    raise_request_exception=True
                )

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(reservation.status, initial_status)
        self.assertEqual(self.book.available_copies, initial_copies)
        self.assertEqual(
            ReservationEvent.objects.filter(
                reservation=reservation
            ).count(),
            initial_events
        )

