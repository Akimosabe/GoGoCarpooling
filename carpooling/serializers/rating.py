from rest_framework import serializers
from carpooling.models import Rating
from .user import UserSerializer


class RatingSerializer(serializers.ModelSerializer):
    """Сериализатор для рейтингов"""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'trip', 'from_user', 'to_user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'from_user', 'created_at']


class RatingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рейтинга"""
    
    class Meta:
        model = Rating
        fields = ['trip', 'to_user', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Проверка значения рейтинга"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5")
        return value
