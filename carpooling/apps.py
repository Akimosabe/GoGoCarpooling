from django.apps import AppConfig
import threading
import time
import logging

logger = logging.getLogger(__name__)


class CarpoolingConfig(AppConfig):
    name = "carpooling"
    verbose_name = "Карпулинг"

    def ready(self):
        """Запускается при старте Django"""
        import os

        # Запускаем только в основном процессе (не в reloader)
        # RUN_MAIN='true' устанавливается reloader'ом Django при автоперезагрузке
        if os.environ.get("RUN_MAIN") == "true":
            self._start_trip_completion_scheduler()

    def _start_trip_completion_scheduler(self):
        """Запускает фоновый поток для автозавершения поездок"""

        def complete_expired_trips_loop():
            """Цикл проверки просроченных поездок каждую минуту"""
            from django.utils import timezone
            from django.db import connection

            print("[Scheduler] Thread started, waiting 10 sec...", flush=True)
            time.sleep(10)
            print("[Scheduler] Starting trip check every 60 sec", flush=True)

            while True:
                try:
                    from carpooling.models import Trip

                    now = timezone.now()
                    expired_trips = Trip.objects.filter(
                        status=Trip.STATUS_ACTIVE, departure_datetime__lt=now
                    )

                    updated = expired_trips.update(status=Trip.STATUS_COMPLETED)

                    if updated > 0:
                        print(
                            f"[Scheduler] Auto-completed {updated} expired trips",
                            flush=True,
                        )

                    # Закрываем соединение, чтобы избежать утечек
                    connection.close()

                except Exception as e:
                    print(f"[Scheduler] Error: {e}", flush=True)

                # Ждём 60 секунд до следующей проверки
                time.sleep(60)

        # Запускаем как daemon-поток (завершится вместе с основным процессом)
        thread = threading.Thread(target=complete_expired_trips_loop, daemon=True)
        thread.start()
        print(
            "[Scheduler] Background thread for trip auto-completion started", flush=True
        )
