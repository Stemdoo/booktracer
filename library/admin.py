from django.contrib import admin
from .models import Author, Genre, Book, UserBookStatus


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
