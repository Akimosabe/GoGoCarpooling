from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpooling', '0012_remove_user_trips_count_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='child_seat_available',
            field=models.BooleanField(default=False, verbose_name='Детское кресло'),
        ),
        migrations.AddField(
            model_name='trip',
            name='two_rear_seats',
            field=models.BooleanField(default=False, verbose_name='2 места на заднем ряду'),
        ),
        migrations.AddField(
            model_name='trip',
            name='parcel_allowed',
            field=models.BooleanField(default=False, verbose_name='Можно посылку'),
        ),
    ]
