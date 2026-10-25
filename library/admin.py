from django.contrib import admin
from .models import Author, Genre, Book, UserBookStatus, BookReservation, ReservationEvent


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'genre')
    search_fields = ('title', 'author__name')
    list_filter = ('genre',)


@admin.register(UserBookStatus)
class UserBookStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'is_favorite')
    list_filter = ('status', 'is_favorite')


@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('book__title', 'user__username')


@admin.register(ReservationEvent)
class ReservationEventAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reservation', 'actor', 'event_type', 'created_at'
    )
    list_filter = ('event_type', 'created_at')
    search_fields = ('details', 'actor__username')