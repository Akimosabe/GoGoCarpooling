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
from carpooling.views import (
    ping,  # Пинг для теста API
    trip_list,  # Список активных поездок (функция с декоратором @api_view)
    trip_detail,  # Детали конкретной поездки по id (функция с декоратором @api_view)
    create_trip,  # Создание новой поездки
    edit_trip,  # Редактирование существующей поездки
    cancel_trip,  # Отмена поездки
    book_seat,  # Бронирование места в поездке
    cancel_booking,  # Отмена бронирования пассажиром или водителем
    user_bookings,  # Список бронирований текущего пользователя
    trip_bookings,  # Список бронирований для конкретной поездки (для водителя)
    register,  # Регистрация пользователя
    login,  # Вход пользователя
    logout,  # Выход пользователя
    current_user,  # Информация о текущем пользователе
)

urlpatterns = [
    # Пинг для теста API
    path('ping/', ping, name='ping'),    # Пинг для теста API
    
    # Аутентификация
    path('auth/register/', register, name='register'),  # Регистрация пользователя
    path('auth/login/', login, name='login'),  # Вход пользователя
    path('auth/logout/', logout, name='logout'),  # Выход пользователя
    path('auth/me/', current_user, name='current-user'),  # Информация о текущем пользователе

    # Поездки
    path('trips/', trip_list, name='trip-list'),  # Список активных поездок
    path('trips/<int:pk>/', trip_detail, name='trip-detail'),  # Детали поездки по id
    path('trips/create/', create_trip, name='create-trip'),  # Создание новой поездки
    path('trips/<int:pk>/edit/', edit_trip, name='edit-trip'),  # Редактирование поездки
    path('trips/<int:pk>/cancel/', cancel_trip, name='cancel-trip'),  # Отмена поездки

    # Бронирования
    path('trips/<int:trip_id>/book/', book_seat, name='book-seat'),  # Бронирование места
    path('bookings/<int:booking_id>/cancel/', cancel_booking, name='cancel-booking'),  # Отмена бронирования
    path('my-bookings/', user_bookings, name='user-bookings'),  # Список бронирований пользователя
    path('trips/<int:trip_id>/bookings/', trip_bookings, name='trip-bookings'),  # Список бронирований для поездки (для водителя)
]
