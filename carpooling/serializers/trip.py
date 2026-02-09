from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import pytz
from carpooling.models import Trip, City, Booking, Car
from .user import UserSerializer, UserDetailSerializer, CarSerializer

User = get_user_model()


class CitySerializer(serializers.ModelSerializer):
    """Сериализатор для городов"""
    class Meta:
        model = City
        fields = [
            'id', 'geoname_id', 'name', 'region', 'country', 'country_code',
            'timezone', 'latitude', 'longitude', 'population', 'is_popular'
        ]


class CityShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для городов (для отображения в поездках)"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'timezone', 'display_name']
    
    def get_display_name(self, obj):
        return f"{obj.name}, {obj.region}"


def _departure_in_origin_tz(obj):
    """Время отправления в часовом поясе города отправления (как указал водитель)."""
    dt = getattr(obj, 'departure_datetime', None)
    if not dt:
        return None
    origin = getattr(obj, 'origin', None)
    tz_name = origin.timezone if origin else 'Europe/Moscow'
    tz = pytz.timezone(tz_name)
    local_dt = dt.astimezone(tz)
    return local_dt.strftime('%d.%m.%Y, %H:%M')


class TripListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка поездок (упрощенный)"""
    driver = UserSerializer(read_only=True)
    driver_rating = serializers.SerializerMethodField()
    car = CarSerializer(read_only=True)
    origin = CityShortSerializer(read_only=True)
    destination = CityShortSerializer(read_only=True)
    departure_datetime = serializers.SerializerMethodField()
    departure_datetime_display = serializers.SerializerMethodField()
    effective_status = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'driver', 'driver_rating', 'car',
            'origin', 'destination', 'departure_datetime', 'departure_datetime_display',
            'price', 'total_seats', 'available_seats',
            'smoking_allowed', 'pets_allowed', 'child_seat_available', 'two_rear_seats', 'parcel_allowed', 'luggage_size',
            'status', 'effective_status', 'is_expired', 'created_at'
        ]

    def get_departure_datetime(self, obj):
        """ISO 8601 для сортировки/фильтров; отображение — departure_datetime_display (время города отправления)."""
        dt = getattr(obj, 'departure_datetime', None)
        return dt.isoformat() if dt else None

    def get_departure_datetime_display(self, obj):
        """Время как ввёл водитель: в поясе города отправления (дд.мм.гггг, чч:мм)."""
        return _departure_in_origin_tz(obj)

    def get_driver_rating(self, obj):
        """Получить рейтинг водителя"""
        return obj.driver.average_rating


class DriverForTripSerializer(serializers.ModelSerializer):
    """Водитель в контексте поездки: телефон только для водителя или пассажира с бронированием"""
    average_rating = serializers.ReadOnlyField()
    total_ratings_count = serializers.ReadOnlyField()
    cars = CarSerializer(many=True, read_only=True)
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'phone', 'avatar', 'date_of_birth',
            'trips_as_driver', 'trips_as_passenger',
            'average_rating', 'total_ratings_count',
            'cars', 'is_staff', 'is_superuser', 'created_at'
        ]

    def get_phone(self, obj):
        request = self.context.get('request')
        trip = self.context.get('trip')
        if not request or not request.user.is_authenticated or not trip:
            return None
        if trip.driver_id == request.user.id:
            return obj.phone
        if trip.bookings.filter(
            passenger=request.user,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
        ).exists():
            return obj.phone
        return None


class TripDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор поездки"""
    driver = serializers.SerializerMethodField()
    car = CarSerializer(read_only=True)
    origin = CityShortSerializer(read_only=True)
    destination = CityShortSerializer(read_only=True)
    departure_datetime = serializers.SerializerMethodField()
    departure_datetime_display = serializers.SerializerMethodField()
    driver_phone = serializers.SerializerMethodField()
    bookings_count = serializers.SerializerMethodField()
    seat_passengers = serializers.SerializerMethodField()
    effective_status = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'driver', 'car',
            'origin', 'destination', 'departure_datetime', 'departure_datetime_display',
            'price', 'total_seats', 'available_seats',
            'description', 'smoking_allowed', 'pets_allowed', 'child_seat_available', 'two_rear_seats', 'parcel_allowed', 'luggage_size',
            'driver_phone', 'bookings_count', 'seat_passengers',
            'status', 'effective_status', 'is_expired', 'created_at', 'updated_at'
        ]

    def get_driver(self, obj):
        context = {**self.context, 'trip': obj}
        return DriverForTripSerializer(obj.driver, context=context).data

    def get_departure_datetime(self, obj):
        dt = getattr(obj, 'departure_datetime', None)
        return dt.isoformat() if dt else None

    def get_departure_datetime_display(self, obj):
        return _departure_in_origin_tz(obj)

    def get_driver_phone(self, obj):
        """Телефон водителя: только для водителя или пассажира с бронированием"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if obj.driver_id == request.user.id:
            return obj.driver.phone
        if obj.bookings.filter(
            passenger=request.user,
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
        ).exists():
            return obj.driver.phone
        return None

    def get_bookings_count(self, obj):
        return obj.bookings.filter(status=Booking.STATUS_CONFIRMED).count()

    def get_seat_passengers(self, obj):
        """Список пассажиров (подтверждённые и ожидающие): аватар для всех, телефон только для водителя"""
        def avatar_name(user):
            a = getattr(user, 'avatar', None)
            if not a:
                return None
            try:
                return a.name
            except (ValueError, AttributeError):
                return None

        bookings = obj.bookings.filter(
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING]
        ).select_related('passenger').order_by('created_at')
        request = self.context.get('request')
        is_driver = request and request.user.is_authenticated and request.user.id == obj.driver_id
        return [
            {
                'booking_id': b.id,
                'passenger': {
                    'id': b.passenger.id,
                    'first_name': b.passenger.first_name or '',
                    'avatar': avatar_name(b.passenger),
                },
                'seats_count': b.seats_count,
                'phone': b.passenger.phone if is_driver else None,
            }
            for b in bookings
        ]


class NewCarSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового автомобиля при создании поездки"""
    class Meta:
        model = Car
        fields = ['brand', 'model', 'year', 'color', 'license_plate']
        extra_kwargs = {
            'license_plate': {'required': False, 'allow_blank': True, 'allow_null': True}
        }


class NaiveDateTimeField(serializers.DateTimeField):
    """
    Поле для даты/времени, которое НЕ добавляет timezone автоматически.
    Время интерпретируется как локальное время города отправления.
    """
    def enforce_timezone(self, value):
        # Не добавляем timezone автоматически - оставляем naive
        # Timezone будет добавлен в validate() на основе города отправления
        return value


class TripCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления поездки"""
    # Можно указать ID существующего автомобиля
    car = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all(), required=False, allow_null=True)
    # Или создать новый автомобиль
    new_car = NewCarSerializer(required=False, write_only=True)
    # Города выбираются по ID
    origin = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    destination = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    # Время без автоматического timezone - будет интерпретировано как время города отправления
    departure_datetime = NaiveDateTimeField()
    
    class Meta:
        model = Trip
        fields = [
            'car', 'new_car', 'origin', 'destination', 'departure_datetime',
            'price', 'total_seats', 'available_seats',
            'description', 'smoking_allowed', 'pets_allowed', 'child_seat_available', 'two_rear_seats', 'parcel_allowed', 'luggage_size'
        ]
    
    def validate_total_seats(self, value):
        """Валидация количества мест"""
        if value < 1 or value > 9:
            raise serializers.ValidationError("Количество мест должно быть от 1 до 9")
        return value
    
    def validate_available_seats(self, value):
        """Валидация доступных мест"""
        if value < 0 or value > 9:
            raise serializers.ValidationError("Количество доступных мест должно быть от 0 до 9")
        return value
    
    def validate(self, data):
        """Валидация данных поездки"""
        # Запрет изменения городов при редактировании
        if self.instance:  # Это UPDATE, не CREATE
            if 'origin' in data:
                raise serializers.ValidationError({
                    'origin': "Нельзя изменить город отправления. Удалите поездку и создайте новую."
                })
            if 'destination' in data:
                raise serializers.ValidationError({
                    'destination': "Нельзя изменить город назначения. Удалите поездку и создайте новую."
                })
        
        if 'available_seats' in data and 'total_seats' in data:
            if data['available_seats'] > data['total_seats']:
                raise serializers.ValidationError(
                    "Доступных мест не может быть больше общего количества мест"
                )
        
        if 'price' in data and data['price'] < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        
        # Проверяем, что города отправления и назначения разные
        origin = data.get('origin')
        destination = data.get('destination')
        if origin and destination and origin == destination:
            raise serializers.ValidationError(
                "Город отправления и город назначения должны быть разными"
            )
        
        # Валидация времени с учётом часового пояса города отправления
        departure_datetime = data.get('departure_datetime')
        if departure_datetime and origin:
            # Получаем часовой пояс города отправления
            origin_tz = pytz.timezone(origin.timezone)
            
            # Текущее время в UTC
            now_utc = datetime.now(pytz.UTC)
            
            # Если время пришло без timezone (naive), считаем его локальным временем города
            if departure_datetime.tzinfo is None:
                # Локализуем время в часовом поясе города отправления
                departure_datetime = origin_tz.localize(departure_datetime)
            
            # Конвертируем в UTC для сравнения и хранения
            departure_utc = departure_datetime.astimezone(pytz.UTC)
            
            if departure_utc < now_utc:
                raise serializers.ValidationError({
                    'departure_datetime': "Нельзя публиковать поездку в прошлом"
                })
            
            # Сохраняем время в UTC
            data['departure_datetime'] = departure_utc
        
        # Проверяем, что указан либо car, либо new_car
        car = data.get('car')
        new_car = data.get('new_car')
        
        if not car and not new_car:
            raise serializers.ValidationError(
                "Необходимо указать существующий автомобиль (car) или данные для нового (new_car)"
            )
        
        if car and new_car:
            raise serializers.ValidationError(
                "Укажите либо существующий автомобиль (car), либо данные для нового (new_car), но не оба"
            )
        
        return data
    
    def validate_car(self, value):
        """Проверяем, что автомобиль принадлежит текущему пользователю"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                if value.owner != request.user:
                    raise serializers.ValidationError("Вы можете использовать только свои автомобили")
        return value
    
    def create(self, validated_data):
        """Создание поездки с автоматической установкой водителя"""
        request = self.context.get('request')
        new_car_data = validated_data.pop('new_car', None)
        
        if request and hasattr(request, 'user'):
            validated_data['driver'] = request.user
            
            # Если указаны данные нового автомобиля, создаём его
            if new_car_data:
                car = Car.objects.create(owner=request.user, **new_car_data)
                validated_data['car'] = car
        
        return super().create(validated_data)
