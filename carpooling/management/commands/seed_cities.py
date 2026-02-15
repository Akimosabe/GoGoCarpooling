"""
Минимальный набор городов для деплоя без Shell (Render free и т.п.).
Данные из carpooling/data/cities_seed.json.
Запуск: python manage.py seed_cities
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from carpooling.models import City


class Command(BaseCommand):
    help = 'Загружает минимальный список городов из cities_seed.json (для деплоя без Shell)'

    def handle(self, *args, **options):
        # __file__ = carpooling/management/commands/seed_cities.py → parent*3 = carpooling/
        path = Path(__file__).resolve().parent.parent.parent / 'data' / 'cities_seed.json'
        if not path.exists():
            self.stderr.write(self.style.ERROR(f'Файл не найден: {path}'))
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created = 0
        with transaction.atomic():
            for row in data:
                _, was_created = City.objects.update_or_create(
                    geoname_id=row['geoname_id'],
                    defaults={
                        'name': row['name'],
                        'region': row['region'],
                        'country': 'Россия',
                        'country_code': 'RU',
                        'timezone': row['timezone'],
                        'population': row.get('population', 0),
                        'is_popular': row.get('population', 0) >= 500000,
                    }
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f'Города загружены. Создано новых: {created}, всего в seed: {len(data)}'))
