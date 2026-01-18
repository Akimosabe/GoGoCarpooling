"""
Management command для автоматического завершения просроченных поездок.

Использование:
    python manage.py complete_expired_trips

Рекомендуется запускать через cron или планировщик задач:
    # Каждую минуту (рекомендуется)
    * * * * * cd /path/to/project && python manage.py complete_expired_trips
    
    # Или через celery beat
    
    # Windows Task Scheduler: создать задачу с триггером "каждую минуту"

Нагрузка:
    Запрос очень лёгкий (~1-5ms), использует индекс по status и departure_datetime.
    Запуск каждую минуту создаёт пренебрежимо малую нагрузку на БД.

Логика:
    departure_datetime хранится в UTC с учётом часового пояса города отправления.
    Сравнение с timezone.now() (UTC) корректно определяет, началась ли поездка.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz
import logging

from carpooling.models import Trip

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Завершает поездки, дата отправления которых уже прошла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие поездки будут завершены, без фактического изменения',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Не выводить сообщения (для запуска по расписанию)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quiet = options['quiet']
        now = timezone.now()
        
        # Находим все активные поездки с датой в прошлом (в UTC)
        # departure_datetime уже хранится в UTC с учётом часового пояса города
        # Запрос использует составной индекс (status, departure_datetime)
        expired_trips = Trip.objects.filter(
            status=Trip.STATUS_ACTIVE,
            departure_datetime__lt=now
        )
        
        count = expired_trips.count()
        
        if count == 0:
            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS('Нет просроченных поездок для завершения')
                )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Найдено {count} просроченных поездок:')
            )
            for trip in expired_trips.select_related('origin', 'destination'):
                # Показываем время в локальном часовом поясе города отправления
                origin_tz = pytz.timezone(trip.origin.timezone)
                local_time = trip.departure_datetime.astimezone(origin_tz)
                self.stdout.write(
                    f'  - ID {trip.id}: {trip.origin.name} → {trip.destination.name} '
                    f'({local_time.strftime("%d.%m.%Y %H:%M")} {trip.origin.timezone})'
                )
        else:
            # Обновляем статус всех просроченных поездок одним запросом
            updated = expired_trips.update(status=Trip.STATUS_COMPLETED)
            
            # Логируем для мониторинга
            if updated > 0:
                logger.info(f'Автозавершено {updated} просроченных поездок')
            
            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS(f'Завершено {updated} просроченных поездок')
                )
