from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from carpooling.models import Notification
from carpooling.serializers import NotificationSerializer


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
    return Response(serializer.data)


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
    return Response({"message": f"Отмечено {count} уведомлений как прочитанных"})
