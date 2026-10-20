from django.urls import path
from . import views

urlpatterns = [
    # старые пути
    path('', views.book_list, name='book_list'),
    path('tabler-test/', views.tabler_test, name='tabler_test'),
    path('books/<int:book_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('my-books/', views.my_books, name='my_books'),
    path('books/<int:book_id>/status/', views.update_book_status, name='update_book_status'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/snippet/', views.book_snippet, name='book_snippet'),

    # новые пути
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/books/', views.api_book_list, name='api_book_list'),
    path('api/books/<int:book_id>/', views.api_book_detail, name='api_book_detail'),
    path('api/genres/', views.api_genres, name='api_genres'),
    path(
        'api/my-book-statuses/',
        views.api_my_book_statuses,
        name='api_my_book_statuses'
    ),
    path(
        'api/my-book-statuses/<int:status_id>/',
        views.api_my_book_status_detail,
        name='api_my_book_status_detail'
    ),
]