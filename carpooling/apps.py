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
        import sys

        # Запускаем планировщик: при runserver — только в дочернем процессе (RUN_MAIN),
        # при gunicorn/uwsgi и т.п. — runserver нет в argv, запускаем в единственном процессе
        run_main = os.environ.get("RUN_MAIN") == "true"
        is_runserver = "runserver" in sys.argv
        if run_main or not is_runserver:
            self._start_trip_completion_scheduler()

    def _start_trip_completion_scheduler(self):
        """Запускает фоновый поток для автозавершения поездок"""

        def complete_expired_trips_loop():
            """Цикл проверки просроченных поездок каждую минуту"""
            from django.db import connection

            print("[Scheduler] Thread started, waiting 10 sec...", flush=True)
            time.sleep(10)
            print("[Scheduler] Starting trip check every 60 sec", flush=True)

            while True:
                try:
                    from carpooling.models import Trip

                    # Просрочка по времени города ОТКУДА (origin)
                    active_trips = Trip.objects.filter(
                        status=Trip.STATUS_ACTIVE
                    ).select_related("origin")
                    expired_trips = [t for t in active_trips if t.is_expired]
                    expired_ids = [t.id for t in expired_trips]
                    updated = (
                        Trip.objects.filter(pk__in=expired_ids).update(
                            status=Trip.STATUS_COMPLETED
                        )
                        if expired_ids
                        else 0
                    )

                    if updated > 0:
                        print(
                            f"[Scheduler] Auto-completed {updated} expired trips",
                            flush=True,
                        )
                    else:
                        print("[Scheduler] Trip check done, 0 expired", flush=True)

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
