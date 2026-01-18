from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import redis
import json

from carpooling.models import Notification
from carpooling.serializers import NotificationSerializer


# Redis клиент
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    """Получение уведомлений текущего пользователя"""
    unread_only = request.query_params.get('unread', 'false').lower() == 'true'
    
    notifications = request.user.notifications.all()
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')[:50]  # Последние 50
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        "unread_count": request.user.notifications.filter(is_read=False).count(),
        "notifications": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_realtime(request):
    """
    Получение новых уведомлений из Redis (для polling).
    Фронтенд может вызывать каждые 5-10 секунд для проверки новых уведомлений.
    """
    user_id = request.user.id
    
    # Получаем уведомления из Redis
    redis_key = f"notifications:unread:{user_id}"
    notifications_json = redis_client.lrange(redis_key, 0, 19)  # Последние 20
    
    notifications = []
    for item in notifications_json:
        try:
            notifications.append(json.loads(item))
        except json.JSONDecodeError:
            continue
    
    return Response({
        "count": len(notifications),
        "notifications": notifications
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_realtime_notifications(request):
    """Очистить уведомления из Redis после прочтения"""
    user_id = request.user.id
    redis_key = f"notifications:unread:{user_id}"
    redis_client.delete(redis_key)
    return Response({"message": "Очередь уведомлений очищена"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({"message": "Уведомление отмечено как прочитанное"})
    except Notification.DoesNotExist:
        return Response({"message": "Уведомление не найдено"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    count = request.user.notifications.filter(is_read=False).update(is_read=True)
    
    # Также очищаем Redis
    user_id = request.user.id
    redis_client.delete(f"notifications:unread:{user_id}")
    
    return Response({"message": f"Отмечено {count} уведомлений как прочитанных"})
