from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def ping(request):
    """Тестовый endpoint для проверки работоспособности API"""
    return Response({
        "status": "ok",
        "message": "GoGoCarpool API is working",
        "version": "1.0"
    }, status=status.HTTP_200_OK)
