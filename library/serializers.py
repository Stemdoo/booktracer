from rest_framework import serializers
from .models import Book, Genre, UserBookStatus, BookReservation, ReservationEvent

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class BookListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author_name',
            'genre_name',
            'available_copies',
        ]

class BookDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)

    class Meta:
        model = Book
        # snippet берется из вашей модели для правого блока
        fields = ['id', 'title', 'description', 'snippet', 'author_name', 'genre_name']



class UserBookStatusSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(
        source='book.title',
        read_only=True
    )
    status_label = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = UserBookStatus
        fields = (
            'id',
            'book',
            'book_title',
            'status',
            'status_label',
            'is_favorite',
        )
        read_only_fields = (
            'id',
            'book_title',
            'status_label',
            'is_favorite',
        )

    def validate(self, attrs):
        if self.instance is None:
            book = attrs.get('book')
            request = self.context.get('request')

            if attrs.get('status', 'to_read') != 'to_read':
                raise serializers.ValidationError({
                    'status': (
                        'Новая запись должна иметь статус '
                        '«Планирую читать».'
                    )
                })

            if book and request and UserBookStatus.objects.filter(
                    user=request.user,
                    book=book
            ).exists():
                raise serializers.ValidationError({
                    'book': 'Эта книга уже есть в вашем списке.'
                })

            return attrs

        old_status = self.instance.status
        new_status = attrs.get('status', old_status)

        allowed_transitions = {
            'to_read': {'reading'},
            'reading': {'read'},
            'read': set(),
        }

        if new_status != old_status:
            if new_status not in allowed_transitions.get(
                    old_status, set()
            ):
                raise serializers.ValidationError({
                    'status': 'Недопустимый переход статуса.'
                })

        return attrs


class ReservationEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(
        source='actor.username',
        read_only=True,
        default=None
    )
    event_label = serializers.CharField(
        source='get_event_type_display',
        read_only=True,
        default=None
    )

    class Meta:
        model = ReservationEvent
        fields = [
            'id',
            'reservation',
            'reservation_id_snapshot',
            'actor',
            'actor_name',
            'event_type',
            'event_label',
            'details',
            'created_at',
        ]
        read_only_fields = fields


class BookReservationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(
        source='book.title',
        read_only=True
    )
    status_label = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = BookReservation
        fields = [
            'id',
            'book',
            'book_title',
            'user',
            'user_name',
            'status',
            'status_label',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_name',
            'status',
            'status_label',
            'created_at',
            'updated_at',
        ]

    def validate_book(self, book):
        request = self.context.get('request')

        # При редактировании разрешаем оставить прежнюю книгу,
        # даже если свободных экземпляров больше нет.
        same_book = (
                self.instance is not None
                and self.instance.book_id == book.id
        )

        if self.instance is not None:
            if self.instance.status != 'created':
                raise serializers.ValidationError(
                    'Книгу можно изменить только у нового бронирования.'
                )

        if not same_book and book.available_copies < 1:
            raise serializers.ValidationError(
                'Нет доступных экземпляров этой книги.'
            )

        if request and BookReservation.objects.filter(
                user=request.user,
                book=book,
                status__in=['created', 'confirmed', 'issued']
        ).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            raise serializers.ValidationError(
                'У вас уже есть активное бронирование этой книги.'
            )

        return book

