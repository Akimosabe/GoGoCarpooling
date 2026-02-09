"""
Django management команда для импорта городов из GeoNames

Использование:
    python manage.py import_geonames

Команда автоматически скачает данные для РФ и стран СНГ из GeoNames,
отфильтрует населённые пункты и загрузит их в базу данных.

Источник данных: https://download.geonames.org/export/dump/
"""

import os
import ssl
import zipfile
import urllib.request
from io import BytesIO
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from carpooling.models import City

# Контекст SSL без верификации (для скачивания с GeoNames)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


# Страны СНГ и их коды ISO
COUNTRIES = {
    'RU': 'Россия',
    'BY': 'Беларусь', 
    'KZ': 'Казахстан',
    'UA': 'Украина',
    'UZ': 'Узбекистан',
    'AZ': 'Азербайджан',
    'AM': 'Армения',
    'GE': 'Грузия',
    'MD': 'Молдова',
    'TJ': 'Таджикистан',
    'KG': 'Кыргызстан',
    'TM': 'Туркменистан',
}

# URL для скачивания кодов регионов
ADMIN1_CODES_URL = "https://download.geonames.org/export/dump/admin1CodesASCII.txt"

# Кэш для кодов регионов (загружается при первом использовании)
_admin1_codes_cache = {}

# Минимальное население для импорта (фильтрует мелкие деревни)
MIN_POPULATION = 5000

# Популярные города (население > 500000)
POPULAR_THRESHOLD = 500000

GEONAMES_URL = "https://download.geonames.org/export/dump/{}.zip"


class Command(BaseCommand):
    help = 'Импорт городов из GeoNames (РФ и страны СНГ)'
    requires_system_checks = []  # Пропускаем проверки (Pillow и т.д.)

    def add_arguments(self, parser):
        parser.add_argument(
            '--countries',
            nargs='+',
            default=['RU'],
            help='Коды стран для импорта (по умолчанию: RU). Доступны: ' + ', '.join(COUNTRIES.keys())
        )
        parser.add_argument(
            '--min-population',
            type=int,
            default=MIN_POPULATION,
            help=f'Минимальное население города (по умолчанию: {MIN_POPULATION})'
        )
        parser.add_argument(
            '--all-cis',
            action='store_true',
            help='Импортировать все страны СНГ'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить таблицу городов перед импортом'
        )

    def handle(self, *args, **options):
        countries = list(COUNTRIES.keys()) if options['all_cis'] else options['countries']
        min_population = options['min_population']
        
        # Валидация кодов стран
        for code in countries:
            if code not in COUNTRIES:
                self.stderr.write(self.style.ERROR(
                    f'Неизвестный код страны: {code}. Доступны: {", ".join(COUNTRIES.keys())}'
                ))
                return
        
        if options['clear']:
            self.stdout.write('Очистка таблицы городов...')
            City.objects.all().delete()
        
        total_created = 0
        total_updated = 0
        
        for country_code in countries:
            country_name = COUNTRIES[country_code]
            self.stdout.write(f'\n{"="*50}')
            self.stdout.write(f'Обработка: {country_name} ({country_code})')
            self.stdout.write(f'{"="*50}')
            
            try:
                created, updated = self.import_country(country_code, country_name, min_population)
                total_created += created
                total_updated += updated
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Ошибка при импорте {country_code}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*50}\n'
            f'ИТОГО: Создано {total_created}, обновлено {total_updated} городов\n'
            f'{"="*50}'
        ))

    def import_country(self, country_code, country_name, min_population):
        """Импорт городов одной страны"""
        
        # Скачиваем ZIP файл
        url = GEONAMES_URL.format(country_code)
        self.stdout.write(f'Скачивание {url}...')
        
        try:
            with urllib.request.urlopen(url, timeout=300, context=SSL_CONTEXT) as response:
                zip_data = BytesIO(response.read())
        except Exception as e:
            raise Exception(f'Не удалось скачать файл: {e}')
        
        # Распаковываем и читаем
        self.stdout.write('Распаковка и обработка...')
        
        cities_to_create = []
        cities_to_update = []
        existing_geoname_ids = set(
            City.objects.filter(country_code=country_code)
            .values_list('geoname_id', flat=True)
        )
        
        with zipfile.ZipFile(zip_data) as zf:
            filename = f'{country_code}.txt'
            with zf.open(filename) as f:
                for line in f:
                    try:
                        row = line.decode('utf-8').strip().split('\t')
                        city_data = self.parse_geonames_row(row, country_code, country_name, min_population)
                        
                        if city_data:
                            if city_data['geoname_id'] in existing_geoname_ids:
                                cities_to_update.append(city_data)
                            else:
                                cities_to_create.append(city_data)
                    except Exception as e:
                        continue  # Пропускаем проблемные строки
        
        # Сохраняем в БД
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            # Создаём новые города
            if cities_to_create:
                City.objects.bulk_create([
                    City(**data) for data in cities_to_create
                ], ignore_conflicts=True)
                created_count = len(cities_to_create)
            
            # Обновляем существующие
            for data in cities_to_update:
                City.objects.filter(geoname_id=data['geoname_id']).update(**data)
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'{country_name}: создано {created_count}, обновлено {updated_count}'
        ))
        
        return created_count, updated_count

    def parse_geonames_row(self, row, country_code, country_name, min_population):
        """Парсинг строки GeoNames"""
        
        # Структура GeoNames:
        # 0: geonameid, 1: name, 2: asciiname, 3: alternatenames,
        # 4: latitude, 5: longitude, 6: feature_class, 7: feature_code,
        # 8: country_code, 9: cc2, 10: admin1_code, 11: admin2_code,
        # 12: admin3_code, 13: admin4_code, 14: population, ...
        
        if len(row) < 15:
            return None
        
        geoname_id = int(row[0])
        name = row[1]
        alternatenames = row[3]  # Альтернативные названия (включая русские)
        feature_class = row[6]
        feature_code = row[7]
        admin1_code = row[10]
        population = int(row[14]) if row[14] else 0
        
        # Фильтруем только населённые пункты (P = populated place)
        # PPL, PPLA, PPLA2, PPLA3, PPLA4, PPLC (столица), PPLS и т.д.
        if feature_class != 'P':
            return None
        
        # Фильтруем по населению
        if population < min_population:
            return None
        
        # Ищем русское название
        russian_name = self.find_russian_name(name, alternatenames)
        
        # Получаем название региона
        region = self.get_region_name(country_code, admin1_code, russian_name)
        # Часовой пояс из выгрузки GeoNames (колонка 17 — IANA timezone id)
        tz_raw = row[17].strip() if len(row) > 17 else ''
        timezone = tz_raw if tz_raw else 'Europe/Moscow'
        
        # Координаты
        try:
            latitude = float(row[4]) if row[4] else None
            longitude = float(row[5]) if row[5] else None
        except ValueError:
            latitude = None
            longitude = None
        
        return {
            'geoname_id': geoname_id,
            'name': russian_name,
            'region': region,
            'country': country_name,
            'country_code': country_code,
            'timezone': timezone,
            'latitude': latitude,
            'longitude': longitude,
            'population': population,
            'is_popular': population >= POPULAR_THRESHOLD,
        }
    
    def find_russian_name(self, name, alternatenames):
        """
        Поиск русского названия.
        Приоритет: ручные исправления > название похожее на английское > первое русское
        """
        
        # Проверяем ручные исправления
        if name in self.CITY_NAME_FIXES:
            return self.CITY_NAME_FIXES[name]
        
        # Если основное название уже на русском — используем его
        if self.is_russian_only(name):
            return name
        
        if not alternatenames:
            return name
        
        # alternatenames — это строка с названиями через запятую
        names = alternatenames.split(',')
        
        # Ищем название только на русском (без специфичных букв других языков)
        russian_candidates = []
        for alt_name in names:
            alt_name = alt_name.strip()
            if alt_name and self.is_russian_only(alt_name):
                # Исключаем устаревшие названия и аббревиатуры
                if len(alt_name) >= 3 and alt_name not in self.OLD_NAMES:
                    russian_candidates.append(alt_name)
        
        if not russian_candidates:
            return name
        
        # Ищем название, наиболее похожее на английское (транслитерация)
        english_lower = name.lower()
        best_match = None
        best_score = -1
        
        for candidate in russian_candidates:
            score = self.transliteration_similarity(candidate, english_lower)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match if best_match else russian_candidates[0]
    
    def transliteration_similarity(self, russian, english):
        """
        Оценка похожести русского названия на английскую транслитерацию.
        Чем выше score, тем больше похоже.
        """
        # Простая транслитерация русского в латиницу
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        
        russian_translit = ''
        for char in russian.lower():
            russian_translit += translit_map.get(char, char)
        
        # Считаем совпадающие символы в начале
        score = 0
        min_len = min(len(russian_translit), len(english))
        for i in range(min_len):
            if russian_translit[i] == english[i]:
                score += 2  # Совпадение в начале важнее
            elif i < 3:
                break  # Первые 3 символа должны совпадать
        
        # Бонус за похожую длину
        len_diff = abs(len(russian_translit) - len(english))
        if len_diff <= 2:
            score += 5
        
        return score
    
    # Устаревшие названия городов, которые нужно пропускать
    OLD_NAMES = {
        'Горький', 'Свердловск', 'Куйбышев', 'Молотов', 'Царицин', 
        'Сталинград', 'Ленинград', 'Калинин', 'Орджоникидзе',
    }
    
    # Ручные исправления названий (английское -> русское)
    CITY_NAME_FIXES = {
        'Moscow': 'Москва',
        'Saint Petersburg': 'Санкт-Петербург',
        'Perm': 'Пермь',
        'Tyumen': 'Тюмень',
        'Kazan': 'Казань',
        'Ryazan': 'Рязань',
        'Tver': 'Тверь',
        'Tomsk': 'Томск',
        'Omsk': 'Омск',
        'Kursk': 'Курск',
        'Pskov': 'Псков',
        'Orel': 'Орёл',
        'Tula': 'Тула',
        'Ufa': 'Уфа',
        'Chita': 'Чита',
        'Penza': 'Пенза',
        'Kerch': 'Керчь',
    }
    
    def is_russian_only(self, text):
        """
        Проверка, что текст написан только русскими буквами.
        Исключаем другие кириллические алфавиты (украинский, чувашский и т.д.)
        """
        if not text:
            return False
            
        # Русские буквы + пробел, дефис, ё, цифры
        russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ -0123456789')
        
        has_russian = False
        for char in text:
            if char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ':
                has_russian = True
            elif char not in russian_chars:
                # Есть символ не из русского алфавита
                return False
        
        return has_russian

    def load_admin1_codes(self):
        """Загрузка кодов регионов из GeoNames"""
        global _admin1_codes_cache
        
        if _admin1_codes_cache:
            return _admin1_codes_cache
        
        self.stdout.write('Загрузка кодов регионов...')
        
        try:
            with urllib.request.urlopen(ADMIN1_CODES_URL, timeout=30, context=SSL_CONTEXT) as response:
                for line in response:
                    row = line.decode('utf-8').strip().split('\t')
                    if len(row) >= 2:
                        # Формат: "RU.48\tLipetsk Oblast\tLipetsk Oblast\t536199"
                        code = row[0]  # "RU.48"
                        name_ascii = row[1]  # "Lipetsk Oblast"
                        # Ищем русское название в alternatenames если есть
                        name = row[2] if len(row) > 2 else name_ascii
                        _admin1_codes_cache[code] = name
        except Exception as e:
            self.stderr.write(f'Не удалось загрузить коды регионов: {e}')
        
        return _admin1_codes_cache
    
    def get_region_name(self, country_code, admin1_code, city_name):
        """Получение названия региона по коду"""
        
        if not admin1_code:
            return city_name
        
        # Загружаем коды регионов
        admin1_codes = self.load_admin1_codes()
        
        # Ключ в формате "RU.48"
        key = f'{country_code}.{admin1_code}'
        region_name = admin1_codes.get(key, '')
        
        if region_name:
            # Преобразуем английское название в русское для России
            if country_code == 'RU':
                return self.translate_region_name(region_name)
            return region_name
        
        return admin1_code or city_name
    
    def translate_region_name(self, english_name):
        """Перевод названия региона с английского на русский"""
        
        # Маппинг английских названий регионов на русские
        translations = {
            'Moscow': 'Москва',
            'Moscow Oblast': 'Московская область',
            'St.-Petersburg': 'Санкт-Петербург',
            'Leningrad Oblast': 'Ленинградская область',
            'Novosibirsk Oblast': 'Новосибирская область',
            'Sverdlovsk Oblast': 'Свердловская область',
            'Nizhny Novgorod Oblast': 'Нижегородская область',
            'Tatarstan Republic': 'Республика Татарстан',
            'Chelyabinsk Oblast': 'Челябинская область',
            'Omsk Oblast': 'Омская область',
            'Samara Oblast': 'Самарская область',
            'Rostov Oblast': 'Ростовская область',
            'Bashkortostan Republic': 'Республика Башкортостан',
            'Krasnoyarsk Krai': 'Красноярский край',
            'Voronezh Oblast': 'Воронежская область',
            'Perm Krai': 'Пермский край',
            'Volgograd Oblast': 'Волгоградская область',
            'Krasnodar Krai': 'Краснодарский край',
            'Saratov Oblast': 'Саратовская область',
            'Tyumen Oblast': 'Тюменская область',
            'Tula Oblast': 'Тульская область',
            'Kemerovo Oblast': 'Кемеровская область',
            'Irkutsk Oblast': 'Иркутская область',
            'Ulyanovsk Oblast': 'Ульяновская область',
            'Yaroslavl Oblast': 'Ярославская область',
            'Khabarovsk Krai': 'Хабаровский край',
            'Primorye': 'Приморский край',
            'Orenburg Oblast': 'Оренбургская область',
            'Penza Oblast': 'Пензенская область',
            'Lipetsk Oblast': 'Липецкая область',
            'Tomsk Oblast': 'Томская область',
            'Ryazan Oblast': 'Рязанская область',
            'Kirov Oblast': 'Кировская область',
            'Astrakhan Oblast': 'Астраханская область',
            'Tver Oblast': 'Тверская область',
            'Kaliningrad Oblast': 'Калининградская область',
            'Belgorod Oblast': 'Белгородская область',
            'Kursk Oblast': 'Курская область',
            'Kaluga Oblast': 'Калужская область',
            'Stavropol Krai': 'Ставропольский край',
            'Ivanovo Oblast': 'Ивановская область',
            'Bryansk Oblast': 'Брянская область',
            'Arkhangelsk Oblast': 'Архангельская область',
            'Vladimir Oblast': 'Владимирская область',
            'Smolensk Oblast': 'Смоленская область',
            'Kurgan Oblast': 'Курганская область',
            'Murmansk Oblast': 'Мурманская область',
            'Orel Oblast': 'Орловская область',
            'Vologda Oblast': 'Вологодская область',
            'Tambov Oblast': 'Тамбовская область',
            'Kostroma Oblast': 'Костромская область',
            'Novgorod Oblast': 'Новгородская область',
            'Pskov Oblast': 'Псковская область',
            'Amur Oblast': 'Амурская область',
            'Sakhalin Oblast': 'Сахалинская область',
            'Magadan Oblast': 'Магаданская область',
            'Kamchatka Krai': 'Камчатский край',
            'Zabaykalsky Krai': 'Забайкальский край',
            'Altai Krai': 'Алтайский край',
            'Altai Republic': 'Республика Алтай',
            'Buryatiya Republic': 'Республика Бурятия',
            'Dagestan Republic': 'Республика Дагестан',
            'Ingushetiya Republic': 'Республика Ингушетия',
            'Kabardino-Balkariya Republic': 'Кабардино-Балкарская Республика',
            'Kalmykiya Republic': 'Республика Калмыкия',
            'Karachayevo-Cherkesiya Republic': 'Карачаево-Черкесская Республика',
            'Kareliya Republic': 'Республика Карелия',
            'Komi Republic': 'Республика Коми',
            'Mariy-El Republic': 'Республика Марий Эл',
            'Mordoviya Republic': 'Республика Мордовия',
            'Sakha Republic': 'Республика Саха (Якутия)',
            'North Ossetia Republic': 'Республика Северная Осетия — Алания',
            'Tyva Republic': 'Республика Тыва',
            'Udmurtiya Republic': 'Удмуртская Республика',
            'Khakasiya Republic': 'Республика Хакасия',
            'Chechnya Republic': 'Чеченская Республика',
            'Chuvashia Republic': 'Чувашская Республика',
            'Adygeya Republic': 'Республика Адыгея',
            'Jewish Autonomous Oblast': 'Еврейская автономная область',
            'Nenets Autonomous Okrug': 'Ненецкий автономный округ',
            'Khanty-Mansiysk': 'Ханты-Мансийский автономный округ',
            'Chukotka': 'Чукотский автономный округ',
            'Yamalo-Nenets': 'Ямало-Ненецкий автономный округ',
            'Crimea Republic': 'Республика Крым',
            'Sevastopol City': 'Севастополь',
            # Дополнительные варианты написания
            'Chelyabinsk': 'Челябинская область',
            'Chelyabinsk Oblast': 'Челябинская область',
            'Rostov': 'Ростовская область',
            'Ulyanovsk': 'Ульяновская область',
            'Khabarovsk': 'Хабаровский край',
            'Nizhny Novgorod': 'Нижегородская область',
        }
        
        return translations.get(english_name, english_name)
