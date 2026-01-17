from django.contrib import admin
from .models import UserProfile, Car, City, Trip, Booking, Rating, Notification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'trips_as_driver', 'trips_as_passenger', 'average_rating', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'total_ratings_count']


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['owner', 'brand', 'model', 'year', 'color', 'license_plate', 'is_active']
    search_fields = ['owner__username', 'brand', 'model', 'license_plate']
    list_filter = ['is_active', 'brand', 'year']
    readonly_fields = ['created_at']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'country', 'is_popular']
    search_fields = ['name', 'region']
    list_filter = ['is_popular', 'country']
    ordering = ['name']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'driver', 'origin', 'destination', 'departure_datetime',
        'price', 'available_seats', 'total_seats', 'status', 'created_at'
    ]
    search_fields = ['driver__username', 'origin', 'destination']
    list_filter = ['status', 'departure_datetime', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'departure_datetime'
    ordering = ['-departure_datetime']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('driver', 'car', 'status')
        }),
        ('Маршрут', {
            'fields': ('origin', 'destination', 'departure_datetime')
        }),
        ('Места и цена', {
            'fields': ('total_seats', 'available_seats', 'price')
        }),
        ('Дополнительно', {
            'fields': ('description', 'smoking_allowed', 'pets_allowed', 'luggage_size')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'trip', 'passenger', 'seats_count', 'status', 'created_at'
    ]
    search_fields = ['passenger__username', 'trip__origin', 'trip__destination']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('trip', 'passenger', 'seats_count', 'status')
        }),
        ('Комментарии', {
            'fields': ('comment', 'rejection_reason')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'rating', 'trip', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    list_filter = ['notification_type', 'is_read', 'created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} уведомлений отмечено как прочитанные')
    mark_as_read.short_description = 'Отметить как прочитанные'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} уведомлений отмечено как непрочитанные')
    mark_as_unread.short_description = 'Отметить как непрочитанные'
