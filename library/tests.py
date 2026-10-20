from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Author, Book, Genre, UserBookStatus


class DeploymentAndApiTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Тестовый автор")
        self.genre = Genre.objects.create(name="Тестовый жанр")
        self.book = Book.objects.create(
            title="Тестовая книга", author=self.author, genre=self.genre
        )
        self.user = User.objects.create_user(username="reader", password="test-pass-123")
        self.client = APIClient()

    def test_healthz_returns_ok(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_book_list_api_returns_database_data(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Тестовая книга")

    def test_invalid_page_returns_bad_request_not_server_error(self):
        response = self.client.get("/api/books/?page=abc")
        self.assertEqual(response.status_code, 400)

    def test_user_can_create_own_book_status(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/my-book-statuses/",
            {"book": self.book.id, "status": "to_read"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            UserBookStatus.objects.filter(user=self.user, book=self.book).exists()
        )

    def test_user_cannot_read_another_users_status(self):
        other = User.objects.create_user(username="other", password="test-pass-123")
        record = UserBookStatus.objects.create(user=other, book=self.book)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/my-book-statuses/{record.id}/")
        self.assertEqual(response.status_code, 404)
