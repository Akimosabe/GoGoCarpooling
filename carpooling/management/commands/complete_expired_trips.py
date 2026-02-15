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
    Просрочка проверяется по времени города ОТКУДА (origin): сравниваем
    «сейчас в городе отправления» с «временем выезда в городе отправления».
"""

from django.core.management.base import BaseCommand
import pytz
import logging

from carpooling.models import Trip
from carpooling.views.utils import create_leave_rating_notifications_for_trip

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

        # Берём все активные поездки и проверяем просрочку по времени города ОТКУДА
        active_trips = Trip.objects.filter(status=Trip.STATUS_ACTIVE).select_related('origin', 'destination')
        expired_trips = [t for t in active_trips if t.is_expired]
        count = len(expired_trips)

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
            for trip in expired_trips:
                origin_tz = pytz.timezone(trip.origin.timezone)
                local_time = trip.departure_datetime.astimezone(origin_tz)
                self.stdout.write(
                    f'  - ID {trip.id}: {trip.origin.name} → {trip.destination.name} '
                    f'({local_time.strftime("%d.%m.%Y %H:%M")} {trip.origin.timezone})'
                )
        else:
            expired_ids = [t.id for t in expired_trips]
            Trip.objects.filter(pk__in=expired_ids).update(status=Trip.STATUS_COMPLETED)
            updated = len(expired_ids)

            # Уведомления «оставить отзыв» участникам завершённых поездок
            for trip in Trip.objects.filter(pk__in=expired_ids).select_related('origin', 'destination').prefetch_related('bookings__passenger'):
                try:
                    create_leave_rating_notifications_for_trip(trip, is_cancelled=False)
                except Exception as e:
                    logger.warning('Ошибка создания уведомлений об отзыве для поездки %s: %s', trip.id, e)

            if updated > 0:
                logger.info(f'Автозавершено {updated} просроченных поездок')

            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS(f'Завершено {updated} просроченных поездок')
                )
