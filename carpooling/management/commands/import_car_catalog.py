"""
Импорт справочника марок и моделей из CSV (popular_cars_russia_150.csv в корне проекта).
Данные попадают в таблицу CarCatalog; в админке «7. Автомобили» можно дополнять вручную.
Потом это поле будет предлагаться по первым символам (автодополнение), писать вручную нельзя,
значение передаётся в автомобиль — старые данные не трогаем.

Использование:
    python manage.py import_car_catalog
"""

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from carpooling.models import CarCatalog

# Файл в корне проекта (рядом с manage.py)
CSV_PATH = Path(settings.BASE_DIR) / "popular_cars_russia_150.csv"


class Command(BaseCommand):
    help = "Импорт марок и моделей из CSV в справочник CarCatalog"

    def handle(self, *args, **options):
        if not CSV_PATH.is_file():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {CSV_PATH}"))
            return

        created = 0
        skipped = 0

        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, fieldnames=["Марка", "Модель"])
            next(reader, None)  # пропуск заголовка
            for row in reader:
                make = (row.get("Марка") or "").strip()[:120]
                model = (row.get("Модель") or "").strip()[:120]
                if not make or not model:
                    skipped += 1
                    continue
                _, was_created = CarCatalog.objects.get_or_create(
                    make=make,
                    model=model,
                    defaults={"make": make, "model": model},
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        CSV_PATH.unlink()
        self.stdout.write(self.style.SUCCESS(f"Добавлено: {created}, уже было/пропущено: {skipped}. Файл удалён."))
