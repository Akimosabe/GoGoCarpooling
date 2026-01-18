from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from carpooling.models import User, Rating, Booking, Trip
from carpooling.serializers import RatingSerializer, RatingCreateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_rating(request):
    """Создание рейтинга после поездки"""
    serializer = RatingCreateSerializer(data=request.data)
    if serializer.is_valid():
        trip = serializer.validated_data['trip']
        to_user = serializer.validated_data['to_user']
        
        # Проверка, что поездка завершена
        if trip.status != Trip.STATUS_COMPLETED:
            return Response({
                "message": "Оценку можно оставить только после завершения поездки"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка, что пользователь участвовал в поездке
        is_driver = trip.driver == request.user
        is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=request.user,
            status=Booking.STATUS_CONFIRMED
        ).exists()
        
        if not (is_driver or is_passenger):
            return Response({
                "message": "Вы не участвовали в этой поездке"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Проверка, что оценивается другой участник поездки
        if to_user == request.user:
            return Response({
                "message": "Вы не можете оценить себя"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка, что to_user тоже участник поездки
        to_user_is_driver = trip.driver == to_user
        to_user_is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=to_user,
            status=Booking.STATUS_CONFIRMED
        ).exists()
        
        if not (to_user_is_driver or to_user_is_passenger):
            return Response({
                "message": "Этот пользователь не участвовал в данной поездке"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создание или обновление рейтинга
        rating, created = Rating.objects.update_or_create(
            trip=trip,
            from_user=request.user,
            to_user=to_user,
            defaults={
                'rating': serializer.validated_data['rating'],
                'comment': serializer.validated_data.get('comment', '')
            }
        )
        
        return Response(
            RatingSerializer(rating).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_ratings(request, user_id):
    """Получение всех рейтингов пользователя"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)
    
    ratings = Rating.objects.filter(to_user=user).select_related('from_user', 'trip')
    serializer = RatingSerializer(ratings, many=True)
    
    return Response({
        "average_rating": user.average_rating,
        "total_count": ratings.count(),
        "ratings": serializer.data
    })
