from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from .models import Book, UserBookStatus, Genre
import urllib.parse
from .serializers import (BookListSerializer, BookDetailSerializer, GenreSerializer, UserBookStatusSerializer,)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status as drf_status


@ensure_csrf_cookie
def book_list(request):
    books = Book.objects.select_related('author', 'genre').all()

    query = request.GET.get('q', '').strip()
    if query:
        books = books.filter(title__icontains=query) | books.filter(
            author__name__icontains=query
        )

    # Фильтрация по жанру
    genre_id = request.GET.get('genre', '')
    if genre_id.isdigit():
        books = books.filter(genre_id=int(genre_id))

    # Сортировка каталога
    sort_option = request.GET.get('sort', 'title')

    if sort_option == 'author':
        books = books.order_by('author__name', 'title')
    else:
        sort_option = 'title'
        books = books.order_by('title')

    genres = Genre.objects.order_by('name')

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            UserBookStatus.objects.filter(
                user=request.user,
                is_favorite=True
            ).values_list('book_id', flat=True)
        )

    return render(request, 'library/book_list.html', {
        'books': books,
        'query': query,
        'favorite_ids': favorite_ids,
        'genres': genres,
        'selected_genre': genre_id,
        'sort_option': sort_option,
        'book_count': books.count(),
    })


def tabler_test(request):
    return render(request, 'library/tabler_test.html')


@login_required
@require_POST
def toggle_favorite(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    status, created = UserBookStatus.objects.get_or_create(
        user=request.user,
        book=book
    )

    status.is_favorite = not status.is_favorite
    status.save(update_fields=['is_favorite'])

    return JsonResponse({
        'is_favorite': status.is_favorite,
        'message': (
            'Книга добавлена в избранное'
            if status.is_favorite
            else 'Книга удалена из избранного'
        )
    })


@login_required(login_url='/admin/login/')
def my_books(request):
    statuses = UserBookStatus.objects.filter(
        user=request.user,
        is_favorite=True
    ).select_related('book__author', 'book__genre')

    return render(request, 'library/my_books.html', {
        'statuses': statuses,
        'status_choices': UserBookStatus.STATUS_CHOICES,
    })


@login_required(login_url='/admin/login/')
@require_POST
def update_book_status(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    new_status = request.POST.get('status')

    valid_statuses = dict(UserBookStatus.STATUS_CHOICES)

    if new_status not in valid_statuses:
        return JsonResponse(
            {'error': 'Некорректный статус'},
            status=400
        )

    status, created = UserBookStatus.objects.get_or_create(
        user=request.user,
        book=book,
    )

    status.status = new_status
    status.save(update_fields=['status'])

    return JsonResponse({
        'success': True,
        'status': status.status,
        'status_label': status.get_status_display(),
    })


def book_detail(request, book_id):
    book = get_object_or_404(
        Book.objects.select_related('author', 'genre'),
        id=book_id
    )
    return render(request, 'library/book_detail.html', {
        'book': book,
    })


def book_snippet(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    return JsonResponse({
        'snippet': book.snippet,
    })


# Добавьте эти импорты в начало файла (или к существующим импортам)
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BookListSerializer, BookDetailSerializer, GenreSerializer



# ИНТЕРАКТИВНЫЙ КАТАЛОГ

def dashboard(request):
    """Отрисовка страницы интерактивного каталога"""
    return render(request, 'library/dashboard.html')


@api_view(['GET'])
def api_genres(request):
    """API: Получение списка жанров для фильтра"""
    genres = Genre.objects.all()
    serializer = GenreSerializer(genres, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_book_list(request):
    """API: Получение списка книг с поиском, фильтром и сортировкой"""
    search = request.GET.get('search', '')
    genre_id = request.GET.get('genre', '')
    ordering = request.GET.get('ordering', '-id')
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        return Response({'error': 'Параметр page должен быть положительным целым числом.'}, status=drf_status.HTTP_400_BAD_REQUEST)
    page_size = 10

    queryset = Book.objects.select_related('author', 'genre').all()

    # 1. Поиск
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(author__name__icontains=search))

    # 2. Фильтрация по жанру
    if genre_id:
        if not genre_id.isdigit():
            return Response({'error': 'Параметр genre должен быть целым числом.'}, status=drf_status.HTTP_400_BAD_REQUEST)
        queryset = queryset.filter(genre__id=int(genre_id))

    # 3. Сортировка
    valid_orderings = ['title', '-title', 'author__name', '-author__name', 'id', '-id']
    if ordering in valid_orderings:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-id')

    # Пагинация
    total_count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    books_page = queryset[start:end]

    serializer = BookListSerializer(books_page, many=True)
    return Response({
        'results': serializer.data,
        'count': total_count,
        'total_pages': (total_count + page_size - 1) // page_size
    })


@api_view(['GET'])
def api_book_detail(request, book_id):
    """API: Получение подробной информации о книге (для правой карточки)"""
    try:
        book = Book.objects.select_related('author', 'genre').get(id=book_id)
        serializer = BookDetailSerializer(book)
        return Response(serializer.data)
    except Book.DoesNotExist:
        return Response({'error': 'Книга не найдена'}, status=404)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_my_book_statuses(request):
    if request.method == 'GET':
        statuses = UserBookStatus.objects.filter(
            user=request.user
        ).select_related('book')

        serializer = UserBookStatusSerializer(
            statuses,
            many=True
        )
        return Response(serializer.data)

    serializer = UserBookStatusSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=drf_status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=drf_status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_my_book_status_detail(request, status_id):
    record = get_object_or_404(
        UserBookStatus,
        id=status_id,
        user=request.user
    )

    if request.method == 'GET':
        serializer = UserBookStatusSerializer(record)
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = UserBookStatusSerializer(
            record,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=drf_status.HTTP_400_BAD_REQUEST
        )

    record.delete()
    return Response(status=drf_status.HTTP_204_NO_CONTENT)
