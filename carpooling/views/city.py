from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Case, When, Value, IntegerField

from carpooling.models import City
from carpooling.serializers import CitySerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request):
    """
    Получение списка городов
    
    Query params:
        - search: поисковый запрос
        - popular: true/false - только популярные города
        - country: код страны (RU, BY, KZ и т.д.)
        - limit: количество результатов (по умолчанию 20, макс 100)
    """
    search = request.query_params.get('search', '')
    popular_only = request.query_params.get('popular', 'false').lower() == 'true'
    country_code = request.query_params.get('country', '')
    
    try:
        limit = min(int(request.query_params.get('limit', 20)), 100)
    except ValueError:
        limit = 20
    
    cities = City.objects.all()
    
    if search:
        cities = cities.filter(
            Q(name__icontains=search) | Q(region__icontains=search)
        )
    
    if popular_only:
        cities = cities.filter(is_popular=True)
    
    if country_code:
        cities = cities.filter(country_code=country_code.upper())
    
    # Сортировка: по населению (крупные города выше)
    cities = cities.order_by('-population', 'name')[:limit]
    
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def city_autocomplete(request):
    """
    Автокомплит городов из локальной базы данных (GeoNames)
    
    Query params:
        - query: поисковый запрос (минимум 2 символа)
        - country: код страны для фильтрации (опционально)
        - limit: количество результатов (по умолчанию 10, макс 20)
    
    Возвращает формат совместимый с DaData для простой миграции фронтенда.
    """
    query = request.query_params.get('query', '').strip()
    country_code = request.query_params.get('country', '')
    
    try:
        limit = min(int(request.query_params.get('limit', 10)), 20)
    except ValueError:
        limit = 10
    
    if not query or len(query) < 2:
        return Response({"suggestions": []})
    
    # Базовый queryset
    cities = City.objects.all()
    
    # Фильтр по стране
    if country_code:
        cities = cities.filter(country_code=country_code.upper())
    
    # Поиск по названию города
    # Приоритет: точное совпадение начала > содержит запрос
    cities = cities.filter(
        Q(name__icontains=query)
    ).annotate(
        # Приоритет сортировки: начинается с запроса = 0, иначе = 1
        search_priority=Case(
            When(name__istartswith=query, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('search_priority', '-population', 'name')[:limit]
    
    # Формируем ответ в формате совместимом с DaData
    suggestions = []
    for city in cities:
        suggestions.append({
            "value": f"{city.name}, {city.region}",
            "data": {
                "id": city.id,
                "city": city.name,
                "region": city.region,
                "country": city.country,
                "country_code": city.country_code,
                "city_with_type": f"г {city.name}",
                "region_with_type": city.region,
                "geo_lat": str(city.latitude) if city.latitude else None,
                "geo_lon": str(city.longitude) if city.longitude else None,
                "population": city.population,
                "geoname_id": city.geoname_id,
            }
        })
    
    return Response({"suggestions": suggestions})
