# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def convert_origin_destination_to_fk(apps, schema_editor):
    """
    Конвертирует текстовые поля origin и destination в ForeignKey на City.
    Для существующих поездок пытается найти город по названию.
    """
    Trip = apps.get_model('carpooling', 'Trip')
    City = apps.get_model('carpooling', 'City')
    
    for trip in Trip.objects.all():
        # Пытаемся найти город отправления
        origin_city = City.objects.filter(name__iexact=trip.origin_text).first()
        if not origin_city:
            # Если не нашли точное совпадение, ищем по частичному
            origin_city = City.objects.filter(name__icontains=trip.origin_text.split(',')[0].strip()).first()
        
        # Пытаемся найти город назначения
        destination_city = City.objects.filter(name__iexact=trip.destination_text).first()
        if not destination_city:
            destination_city = City.objects.filter(name__icontains=trip.destination_text.split(',')[0].strip()).first()
        
        # Если города не найдены, создаём их
        if not origin_city:
            origin_city, _ = City.objects.get_or_create(
                name=trip.origin_text.split(',')[0].strip(),
                defaults={
                    'region': 'Неизвестный регион',
                    'country': 'Россия',
                    'country_code': 'RU'
                }
            )
        
        if not destination_city:
            destination_city, _ = City.objects.get_or_create(
                name=trip.destination_text.split(',')[0].strip(),
                defaults={
                    'region': 'Неизвестный регион',
                    'country': 'Россия',
                    'country_code': 'RU'
                }
            )
        
        trip.origin = origin_city
        trip.destination = destination_city
        trip.save()


def reverse_convert(apps, schema_editor):
    """
    Обратная миграция - конвертирует ForeignKey обратно в текст.
    """
    Trip = apps.get_model('carpooling', 'Trip')
    
    for trip in Trip.objects.select_related('origin', 'destination').all():
        if trip.origin:
            trip.origin_text = f"{trip.origin.name}, {trip.origin.region}"
        if trip.destination:
            trip.destination_text = f"{trip.destination.name}, {trip.destination.region}"
        trip.save()


class Migration(migrations.Migration):

    dependencies = [
        ('carpooling', '0006_city_geonames_fields'),
    ]

    operations = [
        # 1. Переименовываем старые поля
        migrations.RenameField(
            model_name='trip',
            old_name='origin',
            new_name='origin_text',
        ),
        migrations.RenameField(
            model_name='trip',
            old_name='destination',
            new_name='destination_text',
        ),
        
        # 2. Добавляем новые FK поля (nullable для начала)
        migrations.AddField(
            model_name='trip',
            name='origin',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='trips_from',
                to='carpooling.City',
                verbose_name='Откуда'
            ),
        ),
        migrations.AddField(
            model_name='trip',
            name='destination',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='trips_to',
                to='carpooling.City',
                verbose_name='Куда'
            ),
        ),
        
        # 3. Конвертируем данные
        migrations.RunPython(convert_origin_destination_to_fk, reverse_convert),
        
        # 4. Делаем поля обязательными
        migrations.AlterField(
            model_name='trip',
            name='origin',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='trips_from',
                to='carpooling.City',
                verbose_name='Откуда'
            ),
        ),
        migrations.AlterField(
            model_name='trip',
            name='destination',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='trips_to',
                to='carpooling.City',
                verbose_name='Куда'
            ),
        ),
        
        # 5. Удаляем старые текстовые поля
        migrations.RemoveField(
            model_name='trip',
            name='origin_text',
        ),
        migrations.RemoveField(
            model_name='trip',
            name='destination_text',
        ),
        
        # 6. Обновляем verbose_name для остальных полей
        migrations.AlterField(
            model_name='trip',
            name='driver',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='driven_trips',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Водитель'
            ),
        ),
        migrations.AlterField(
            model_name='trip',
            name='car',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='trips',
                to='carpooling.Car',
                verbose_name='Автомобиль'
            ),
        ),
        migrations.AlterField(
            model_name='trip',
            name='departure_datetime',
            field=models.DateTimeField(verbose_name='Дата и время отправления'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Цена за место'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='total_seats',
            field=models.PositiveIntegerField(verbose_name='Всего мест'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='available_seats',
            field=models.PositiveIntegerField(verbose_name='Доступно мест'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание поездки'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='smoking_allowed',
            field=models.BooleanField(default=False, verbose_name='Можно курить'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='pets_allowed',
            field=models.BooleanField(default=False, verbose_name='Можно с животными'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='luggage_size',
            field=models.CharField(
                choices=[('small', 'Малый'), ('medium', 'Средний'), ('large', 'Большой')],
                default='medium',
                max_length=20,
                verbose_name='Размер багажа'
            ),
        ),
        migrations.AlterField(
            model_name='trip',
            name='status',
            field=models.CharField(
                choices=[('active', 'Активна'), ('cancelled', 'Отменена'), ('completed', 'Завершена')],
                default='active',
                max_length=20,
                verbose_name='Статус'
            ),
        ),
        migrations.AlterField(
            model_name='trip',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создано'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
    ]
