from rest_framework import serializers
from .models import Book, Genre, UserBookStatus

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class BookListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author_name', 'genre_name']

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

            if book and request and UserBookStatus.objects.filter(
                    user=request.user,
                    book=book
            ).exists():
                raise serializers.ValidationError({
                    'book': 'Эта книга уже есть в вашем списке.'
                })

        return attrs

