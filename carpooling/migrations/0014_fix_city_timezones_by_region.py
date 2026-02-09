# Исправляет таймзоны у городов, загруженных до перехода на таймзону из GeoNames
# (например Екатеринбург мог остаться с Europe/Moscow вместо Asia/Yekaterinburg)

from django.db import migrations


def set_timezone_by_region(apps, schema_editor):
    """Выставляет часовой пояс по региону для уже существующих городов."""
    City = apps.get_model('carpooling', 'City')
    region_timezone_map = {
        'Калининградская область': 'Europe/Kaliningrad',
        'Москва': 'Europe/Moscow',
        'Московская область': 'Europe/Moscow',
        'Санкт-Петербург': 'Europe/Moscow',
        'Ленинградская область': 'Europe/Moscow',
        'Республика Крым': 'Europe/Moscow',
        'Севастополь': 'Europe/Moscow',
        'Краснодарский край': 'Europe/Moscow',
        'Ростовская область': 'Europe/Moscow',
        'Воронежская область': 'Europe/Moscow',
        'Белгородская область': 'Europe/Moscow',
        'Курская область': 'Europe/Moscow',
        'Липецкая область': 'Europe/Moscow',
        'Тамбовская область': 'Europe/Moscow',
        'Орловская область': 'Europe/Moscow',
        'Брянская область': 'Europe/Moscow',
        'Калужская область': 'Europe/Moscow',
        'Тульская область': 'Europe/Moscow',
        'Рязанская область': 'Europe/Moscow',
        'Владимирская область': 'Europe/Moscow',
        'Ивановская область': 'Europe/Moscow',
        'Костромская область': 'Europe/Moscow',
        'Ярославская область': 'Europe/Moscow',
        'Тверская область': 'Europe/Moscow',
        'Смоленская область': 'Europe/Moscow',
        'Псковская область': 'Europe/Moscow',
        'Новгородская область': 'Europe/Moscow',
        'Вологодская область': 'Europe/Moscow',
        'Архангельская область': 'Europe/Moscow',
        'Мурманская область': 'Europe/Moscow',
        'Республика Карелия': 'Europe/Moscow',
        'Республика Коми': 'Europe/Moscow',
        'Ненецкий автономный округ': 'Europe/Moscow',
        'Нижегородская область': 'Europe/Moscow',
        'Республика Мордовия': 'Europe/Moscow',
        'Чувашская Республика': 'Europe/Moscow',
        'Республика Марий Эл': 'Europe/Moscow',
        'Кировская область': 'Europe/Moscow',
        'Пензенская область': 'Europe/Moscow',
        'Волгоградская область': 'Europe/Moscow',
        'Астраханская область': 'Europe/Moscow',
        'Республика Калмыкия': 'Europe/Moscow',
        'Республика Дагестан': 'Europe/Moscow',
        'Чеченская Республика': 'Europe/Moscow',
        'Республика Ингушетия': 'Europe/Moscow',
        'Республика Северная Осетия — Алания': 'Europe/Moscow',
        'Кабардино-Балкарская Республика': 'Europe/Moscow',
        'Карачаево-Черкесская Республика': 'Europe/Moscow',
        'Ставропольский край': 'Europe/Moscow',
        'Республика Адыгея': 'Europe/Moscow',
        'Самарская область': 'Europe/Samara',
        'Удмуртская Республика': 'Europe/Samara',
        'Ульяновская область': 'Europe/Samara',
        'Саратовская область': 'Europe/Samara',
        'Свердловская область': 'Asia/Yekaterinburg',
        'Челябинская область': 'Asia/Yekaterinburg',
        'Курганская область': 'Asia/Yekaterinburg',
        'Оренбургская область': 'Asia/Yekaterinburg',
        'Пермский край': 'Asia/Yekaterinburg',
        'Республика Башкортостан': 'Asia/Yekaterinburg',
        'Тюменская область': 'Asia/Yekaterinburg',
        'Ханты-Мансийский автономный округ': 'Asia/Yekaterinburg',
        'Ямало-Ненецкий автономный округ': 'Asia/Yekaterinburg',
        'Омская область': 'Asia/Omsk',
        'Новосибирская область': 'Asia/Krasnoyarsk',
        'Томская область': 'Asia/Krasnoyarsk',
        'Алтайский край': 'Asia/Krasnoyarsk',
        'Республика Алтай': 'Asia/Krasnoyarsk',
        'Кемеровская область': 'Asia/Krasnoyarsk',
        'Красноярский край': 'Asia/Krasnoyarsk',
        'Республика Хакасия': 'Asia/Krasnoyarsk',
        'Республика Тыва': 'Asia/Krasnoyarsk',
        'Иркутская область': 'Asia/Irkutsk',
        'Республика Бурятия': 'Asia/Irkutsk',
        'Республика Саха (Якутия)': 'Asia/Yakutsk',
        'Забайкальский край': 'Asia/Yakutsk',
        'Амурская область': 'Asia/Yakutsk',
        'Приморский край': 'Asia/Vladivostok',
        'Хабаровский край': 'Asia/Vladivostok',
        'Еврейская автономная область': 'Asia/Vladivostok',
        'Сахалинская область': 'Asia/Vladivostok',
        'Магаданская область': 'Asia/Magadan',
        'Камчатский край': 'Asia/Kamchatka',
        'Чукотский автономный округ': 'Asia/Kamchatka',
    }
    for city in City.objects.all():
        tz = region_timezone_map.get(city.region, 'Europe/Moscow')
        city.timezone = tz
        city.save(update_fields=['timezone'])


class Migration(migrations.Migration):

    dependencies = [
        ('carpooling', '0013_trip_child_seat_rear_seats_parcel'),
    ]

    operations = [
        migrations.RunPython(set_timezone_by_region, migrations.RunPython.noop),
    ]
