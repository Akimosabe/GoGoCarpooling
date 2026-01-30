"""
WSGI config for GoGoCarpool project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

# Загружаем hiddensettings.env до импорта Django (если есть файл и установлен python-dotenv)
_root = Path(__file__).resolve().parent.parent
_env_file = _root / 'hiddensettings.env'
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GoGoCarpool.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
