# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Добавляет составной индекс (status, departure_datetime) для оптимизации:
    - Автозакрытия просроченных поездок (complete_expired_trips)
    - Поиска активных поездок в будущем (trip_list view)
    """

    dependencies = [
        ('carpooling', '0008_city_timezone'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='trip',
            index=models.Index(
                fields=['status', 'departure_datetime'],
                name='trip_status_departure_idx'
            ),
        ),
    ]
