from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from .models import Book, UserBookStatus, Genre, BookReservation, ReservationEvent
import urllib.parse
from .serializers import (BookListSerializer, BookDetailSerializer, GenreSerializer,
                          UserBookStatusSerializer, BookReservationSerializer, ReservationEventSerializer,)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.db.models import Q


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
    page = int(request.GET.get('page', 1))
    page_size = 10

    queryset = Book.objects.select_related('author', 'genre').all()

    # 1. Поиск
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(author__name__icontains=search))

    # 2. Фильтрация по жанру
    if genre_id:
        queryset = queryset.filter(genre__id=genre_id)

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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_reservations(request):
    if request.method == 'GET':
        reservations = BookReservation.objects.filter(
            user=request.user
        ).select_related('book', 'user')

        # Фильтр по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            valid_statuses = dict(BookReservation.STATUS_CHOICES)
            if status_filter not in valid_statuses:
                return Response(
                    {'error': 'Неизвестный статус.'},
                    status=drf_status.HTTP_400_BAD_REQUEST
                )
            reservations = reservations.filter(status=status_filter)

        # Фильтр по жанру книги
        genre_filter = request.query_params.get('genre')
        if genre_filter:
            if not genre_filter.isdigit():
                return Response(
                    {'error': 'Некорректный жанр.'},
                    status=drf_status.HTTP_400_BAD_REQUEST
                )
            reservations = reservations.filter(
                book__genre_id=int(genre_filter)
            )

        serializer = BookReservationSerializer(
            reservations.order_by('-created_at'),
            many=True
        )
        return Response(serializer.data)

    serializer = BookReservationSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        with transaction.atomic():
            reservation = serializer.save(user=request.user)
            ReservationEvent.objects.create(
                reservation=reservation,
                reservation_id_snapshot=reservation.id,
                actor=request.user,
                event_type='created',
                details='Создано новое бронирование.'
            )

        return Response(
            BookReservationSerializer(reservation).data,
            status=drf_status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=drf_status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_reservation_detail(request, reservation_id):
    reservation = get_object_or_404(
        BookReservation.objects.select_related('book', 'user'),
        id=reservation_id,
        user=request.user
    )

    if request.method == 'GET':
        return Response(BookReservationSerializer(reservation).data)

    if request.method in ['PUT', 'PATCH']:
        serializer = BookReservationSerializer(
            reservation,
            data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=drf_status.HTTP_400_BAD_REQUEST
            )

        if reservation.status != 'created':
            return Response(
                {'error': 'Изменять можно только новое бронирование.'},
                status=drf_status.HTTP_400_BAD_REQUEST
            )

        old_book_id = reservation.book_id

        with transaction.atomic():
            reservation = serializer.save()

            if reservation.book_id != old_book_id:
                ReservationEvent.objects.create(
                    reservation=reservation,
                    actor=request.user,
                    event_type='updated',
                    details='Изменена книга в бронировании.'
                )

        return Response(BookReservationSerializer(reservation).data)

    # Удаление разрешено только для ещё не подтверждённого бронирования.
    if reservation.status != 'created':
        return Response(
            {'error': 'Удалить можно только новое бронирование.'},
            status=drf_status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        reservation_id = reservation.id

        # Сохраняем номер бронирования в истории событий.
        reservation.events.filter(
            reservation_id_snapshot__isnull=True
        ).update(reservation_id_snapshot=reservation_id)

        # Создаём событие об удалении.
        ReservationEvent.objects.create(
            reservation=None,
            reservation_id_snapshot=reservation_id,
            actor=request.user,
            event_type='deleted',
            details='Бронирование удалено.'
        )

        reservation.delete()

    return Response(status=drf_status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reservation_action(request, reservation_id):
    action = request.data.get('action')

    allowed_actions = {
        'confirm': ('created', 'confirmed'),
        'issue': ('confirmed', 'issued'),
        'return': ('issued', 'returned'),
        'cancel': (('created', 'confirmed'), 'cancelled'),
    }

    if action not in allowed_actions:
        return Response(
            {'error': 'Неизвестная операция.'},
            status=drf_status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            reservation = get_object_or_404(
                BookReservation.objects.select_for_update(),
                id=reservation_id,
                user=request.user
            )

            book = Book.objects.select_for_update().get(
                id=reservation.book_id
            )

            old_status, new_status = allowed_actions[action]

            if isinstance(old_status, tuple):
                allowed = reservation.status in old_status
            else:
                allowed = reservation.status == old_status

            if not allowed:
                raise ValidationError(
                    'Этот переход статуса запрещён.'
                )

            if action == 'confirm':
                if book.available_copies < 1:
                    raise ValidationError(
                        'Нет доступных экземпляров книги.'
                    )
                book.available_copies -= 1
                book.save(update_fields=['available_copies'])

            elif action == 'return':
                book.available_copies += 1
                book.save(update_fields=['available_copies'])

            elif action == 'cancel':
                # При отмене подтверждённого бронирования
                # возвращаем экземпляр в доступный остаток.
                if reservation.status == 'confirmed':
                    book.available_copies += 1
                    book.save(update_fields=['available_copies'])

            reservation.status = new_status
            reservation.save(update_fields=['status', 'updated_at'])

            event_labels = {
                'confirm': 'Бронирование подтверждено.',
                'issue': 'Книга выдана.',
                'return': 'Книга возвращена.',
                'cancel': 'Бронирование отменено.',
            }

            ReservationEvent.objects.create(
                reservation=reservation,
                reservation_id_snapshot=reservation.id,
                actor=request.user,
                event_type=action,
                details=event_labels[action]
            )

    except ValidationError as error:
        return Response(
            {'error': error.detail},
            status=drf_status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'message': event_labels[action],
        'reservation': BookReservationSerializer(reservation).data,
        'available_copies': book.available_copies,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_reservation_events(request, reservation_id):
    reservation = get_object_or_404(
        BookReservation,
        id=reservation_id,
        user=request.user
    )

    events = reservation.events.select_related('actor').all()
    serializer = ReservationEventSerializer(events, many=True)

    return Response(serializer.data)


@login_required
def reservations_page(request):
    return render(request, 'library/reservations.html')