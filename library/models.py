from django.db import models
from django.contrib.auth.models import User


# 1. Модель Автора
class Author(models.Model):
    name = models.CharField(max_length=200, verbose_name="Имя автора")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"


# 2. Модель Жанра
class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название жанра")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"


# 3. Модель Книги
class Book(models.Model):
    title = models.CharField(max_length=300, verbose_name="Название книги")
    description = models.TextField(verbose_name="Описание", blank=True)
    # Фрагмент книги для чтения без перезагрузки (требование СРС)
    snippet = models.TextField(verbose_name="Фрагмент для чтения", blank=True)

    available_copies = models.PositiveIntegerField(
        default=1,
        verbose_name="Доступные экземпляры"
    )

    # Связь: У одного автора может быть много книг (ForeignKey)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books', verbose_name="Автор")
    # Связь: У одного жанра может быть много книг
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='books', verbose_name="Жанр")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"


# 4. Модель связи Пользователя и Книги (Статус чтения)
class UserBookStatus(models.Model):
    STATUS_CHOICES = [
        ('to_read', 'Планирую читать'),
        ('reading', 'Читаю сейчас'),
        ('read', 'Прочитано'),
    ]

    # Связь: У одного пользователя может быть много записей о разных книгах
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_statuses', verbose_name="Пользователь")
    # Связь: У одной книги может быть много пользователей, которые её читают
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='user_statuses', verbose_name="Книга")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_read', verbose_name="Статус")
    is_favorite = models.BooleanField(default=False, verbose_name="В избранном")

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Статус книги у пользователя"
        verbose_name_plural = "Статусы книг у пользователей"
        # Запрещаем пользователю иметь две одинаковые записи для одной и той же книги
        unique_together = ('user', 'book')



class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создано'),
        ('confirmed', 'Подтверждено'),
        ('issued', 'Выдано'),
        ('returned', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Книга"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='book_reservations',
        verbose_name="Пользователь"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name="Статус бронирования"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )

    def __str__(self):
        return f"{self.book.title} — {self.get_status_display()}"

    class Meta:
        verbose_name = "Бронирование книги"
        verbose_name_plural = "Бронирования книг"



class ReservationEvent(models.Model):
    reservation = models.ForeignKey(
        BookReservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name="Бронирование"
    )

    reservation_id_snapshot = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Номер бронирования"
    )

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Инициатор"
    )

    event_type = models.CharField(
        max_length=50,
        verbose_name="Тип события"
    )

    details = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Описание события"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата события"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = "Событие бронирования"
        verbose_name_plural = "История бронирований"

    def __str__(self):
        return f"{self.event_type} — {self.reservation}"
