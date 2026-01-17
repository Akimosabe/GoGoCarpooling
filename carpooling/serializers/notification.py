from rest_framework import serializers
from carpooling.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'trip', 'booking', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
