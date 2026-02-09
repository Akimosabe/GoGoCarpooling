from .auth import (
    register, login, logout, current_user,
    password_reset_request, password_reset_confirm,
    change_password, delete_account
)
from .user import (
    user_profile, update_profile,
    car_list_create, car_detail,
    car_catalog_autocomplete
)
from .city import city_list, city_autocomplete
from .trip import (
    trip_list, trip_detail, create_trip,
    edit_trip, cancel_trip, my_trips
)
from .booking import (
    book_seat, cancel_booking, reject_booking,
    user_bookings, trip_bookings
)
from .rating import create_rating, user_ratings
from .notification import (
    notifications_list, notifications_realtime,
    clear_realtime_notifications, mark_notification_read,
    mark_all_notifications_read
)
from .ping import ping
from .utils import create_notification

__all__ = [
    # Auth views
    'register', 'login', 'logout', 'current_user',
    'password_reset_request', 'password_reset_confirm',
    'change_password', 'delete_account',
    # User views
    'user_profile', 'update_profile',
    'car_list_create', 'car_detail',
    'car_catalog_autocomplete',
    # City views
    'city_list', 'city_autocomplete',
    # Trip views
    'trip_list', 'trip_detail', 'create_trip',
    'edit_trip', 'cancel_trip', 'my_trips',
    # Booking views
    'book_seat', 'cancel_booking', 'reject_booking',
    'user_bookings', 'trip_bookings',
    # Rating views
    'create_rating', 'user_ratings',
    # Notification views
    'notifications_list', 'notifications_realtime',
    'clear_realtime_notifications', 'mark_notification_read',
    'mark_all_notifications_read',
    # Ping view
    'ping',
    # Utils
    'create_notification',
]
