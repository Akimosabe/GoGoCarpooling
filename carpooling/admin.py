from django.contrib import admin
from .models import Trip, Booking


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "driver",
        "origin",
        "destination",
        "departure_datetime",
        "price",
        "available_seats",
        "status",
    )

    list_filter = (
        "status",
        "departure_datetime",
    )

    search_fields = (
        "origin",
        "destination",
        "driver__username",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    ("driver", "status"),
                    ("origin", "destination"),
                    "departure_datetime",
                )
            },
        ),
        ("Места и цена", {"fields": (("price", "total_seats", "available_seats"),)}),
        ("Служебная информация", {"fields": ("created_at",)}),
    )

    readonly_fields = ("created_at",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "trip",
        "passenger",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "passenger__username",
        "trip__origin",
        "trip__destination",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)
