"""
URL configuration for GoGoCarpool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from carpooling.views import (
    # Утилиты
    ping,
    
    # Аутентификация
    register,
    login,
    logout,
    current_user,
    password_reset_request,
    password_reset_confirm,
    
    # Профили
    user_profile,
    update_profile,
    car_list_create,
    car_detail,
    
    # Города
    city_list,
    city_autocomplete,
    
    # Поездки
    trip_list,
    trip_detail,
    create_trip,
    edit_trip,
    cancel_trip,
    my_trips,
    
    # Бронирования
    book_seat,
    cancel_booking,
    reject_booking,
    user_bookings,
    trip_bookings,
    
    # Рейтинги
    create_rating,
    user_ratings,
    
    # Уведомления
    notifications_list,
    mark_notification_read,
    mark_all_notifications_read,
)

urlpatterns = [
    # ============ Утилиты ============
    path('api/ping/', ping, name='ping'),
    
    # ============ Аутентификация ============
    path('api/auth/register/', register, name='register'),
    path('api/auth/login/', login, name='login'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/auth/me/', current_user, name='current-user'),
    path('api/auth/password-reset/', password_reset_request, name='password-reset-request'),
    path('api/auth/password-reset/<str:uidb64>/<str:token>/', password_reset_confirm, name='password-reset-confirm'),
    
    # ============ Профили пользователей ============
    path('api/users/<int:user_id>/profile/', user_profile, name='user-profile'),
    path('api/profile/update/', update_profile, name='update-profile'),
    
    # ============ Управление автомобилями ============
    path('api/cars/', car_list_create, name='car-list-create'),
    path('api/cars/<int:car_id>/', car_detail, name='car-detail'),
    
    # ============ Города ============
    path('api/cities/', city_list, name='city-list'),
    path('api/cities/autocomplete/', city_autocomplete, name='city-autocomplete'),
    
    # ============ Поездки ============
    path('api/trips/', trip_list, name='trip-list'),
    path('api/trips/<int:trip_id>/', trip_detail, name='trip-detail'),
    path('api/trips/create/', create_trip, name='create-trip'),
    path('api/trips/<int:trip_id>/edit/', edit_trip, name='edit-trip'),
    path('api/trips/<int:trip_id>/cancel/', cancel_trip, name='cancel-trip'),
    path('api/my-trips/', my_trips, name='my-trips'),
    
    # ============ Бронирования ============
    path('api/trips/<int:trip_id>/book/', book_seat, name='book-seat'),
    path('api/bookings/<int:booking_id>/cancel/', cancel_booking, name='cancel-booking'),
    path('api/bookings/<int:booking_id>/reject/', reject_booking, name='reject-booking'),
    path('api/my-bookings/', user_bookings, name='user-bookings'),
    path('api/trips/<int:trip_id>/bookings/', trip_bookings, name='trip-bookings'),
    
    # ============ Рейтинги ============
    path('api/ratings/create/', create_rating, name='create-rating'),
    path('api/users/<int:user_id>/ratings/', user_ratings, name='user-ratings'),
    
    # ============ Уведомления ============
    path('api/notifications/', notifications_list, name='notifications-list'),
    path('api/notifications/<int:notification_id>/read/', mark_notification_read, name='mark-notification-read'),
    path('api/notifications/read-all/', mark_all_notifications_read, name='mark-all-notifications-read'),
    
    # ============ Админка ============
    path('admin/', admin.site.urls),
]

# Для загрузки медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
