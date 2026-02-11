import re

from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from carpooling.models import User, Car, CarCatalog, Booking
from carpooling.serializers import (
    UserDetailSerializer, UserProfileSerializer, CarSerializer
)


def _mask_phone(phone):
    """Маска номера: видны только последние 2 цифры, остальное ***"""
    if not phone or not str(phone).strip():
        return None
    s = str(phone).strip()
    digits = re.findall(r'\d', s)
    if len(digits) < 2:
        return '+7 *** *** ** **'
    visible = ''.join(digits[-2:])
    return '+7 *** *** ** ' + visible


def _mask_email(email):
    """Маска почты: первый символ + *** @ *** . домен"""
    if not email or not str(email).strip():
        return None
    s = str(email).strip()
    if '@' not in s:
        return '***@***.***'
    local, rest = s.split('@', 1)
    if not local:
        return '***@***.***'
    domain = rest.rsplit('.', 1)
    tld = domain[-1] if len(domain) > 1 else '***'
    return f'{local[0]}***@***.{tld}'


@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile(request, user_id):
    """Получение профиля пользователя. Номер показываем только себе или при общем бронировании."""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserDetailSerializer(user, context={'request': request})
        data = serializer.data
        # Номер виден: владельцу профиля или тому, кто забронирован в поездку этого пользователя (как водителя)
        can_see_phone = (
            request.user.is_authenticated
            and (
                request.user.id == user_id
                or Booking.objects.filter(
                    trip__driver_id=user_id,
                    passenger=request.user,
                    status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING],
                ).exists()
            )
        )
        if not can_see_phone and data.get('phone'):
            data['phone'] = _mask_phone(user.phone)
            data['phone_masked'] = True
        else:
            data['phone_masked'] = False
        if not can_see_phone and data.get('email'):
            data['email'] = _mask_email(user.email)
            data['email_masked'] = True
        else:
            data['email_masked'] = False
        return Response(data)
    except User.DoesNotExist:
        return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Обновление профиля текущего пользователя. POST — для загрузки аватарки (multipart), PUT — без файла."""
    if request.method == 'POST' and request.content_type and 'multipart' in request.content_type:
        data = {**request.POST.dict()}
        if request.FILES.get('avatar'):
            data['avatar'] = request.FILES['avatar']
    else:
        data = request.data
    serializer = UserProfileSerializer(
        request.user,
        data=data,
        partial=True,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def car_list_create(request):
    """Получение списка машин пользователя или создание новой"""
    if request.method == 'GET':
        cars = request.user.cars.all()
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def car_detail(request, car_id):
    """Обновление или удаление машины"""
    try:
        car = Car.objects.get(id=car_id, owner=request.user)
    except Car.DoesNotExist:
        return Response({"message": "Автомобиль не найден"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = CarSerializer(car, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        car.delete()
        return Response({"message": "Автомобиль удален"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def car_catalog_autocomplete(request):
    """Поиск марка+модель по первым буквам. Только из справочника."""
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'results': []})
    qs = CarCatalog.objects.filter(
        Q(make__icontains=q) | Q(model__icontains=q)
    ).order_by('make', 'model')[:25]
    results = [{'make': c.make, 'model': c.model} for c in qs]
    return Response({'results': results})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_user(request, user_id):
    """Отправка жалобы на пользователя. Письмо уходит на REPORT_EMAIL."""
    text = (request.data.get('text') or '').strip()
    if not text:
        return Response(
            {"message": "Опишите причину жалобы"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if request.user.id == user_id:
        return Response(
            {"message": "Нельзя пожаловаться на себя"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        reported = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"message": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )
    reporter_name = request.user.first_name or request.user.email or str(request.user.id)
    reported_name = reported.first_name or reported.email or str(reported.id)
    body = (
        f"Кто пожаловался: {reporter_name} ({request.user.id})\n"
        f"На кого: {reported_name} ({reported.id})\n\n"
        f"{text}"
    )
    send_mail(
        subject="Жалоба на пользователя GoGoCarpool",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[getattr(settings, 'REPORT_EMAIL', 'akimo7abe@gmail.com')],
        fail_silently=False,
    )
    return Response({"message": "Жалоба отправлена"})
