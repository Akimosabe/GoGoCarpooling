from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.conf import settings
import requests

from carpooling.models import City
from carpooling.serializers import CitySerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request):
    """Получение списка городов"""
    search = request.query_params.get('search', '')
    popular_only = request.query_params.get('popular', 'false').lower() == 'true'
    
    cities = City.objects.all()
    
    if search:
        cities = cities.filter(
            Q(name__icontains=search) | Q(region__icontains=search)
        )
    
    if popular_only:
        cities = cities.filter(is_popular=True)
    
    cities = cities[:20]  # Ограничение результатов
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def city_autocomplete(request):
    """Автокомплит городов через Dadata API"""
    
    query = request.query_params.get('query', '')
    
    if not query or len(query) < 2:
        return Response({
            "suggestions": []
        })
    
    # Проверяем наличие API ключа
    api_key = settings.DADATA_API_KEY
    secret_key = settings.DADATA_SECRET_KEY
    
    if not api_key or not secret_key:
        # Если нет ключей Dadata, используем локальную БД
        cities = City.objects.filter(
            Q(name__icontains=query)
        )[:10]
        
        suggestions = []
        for city in cities:
            suggestions.append({
                "value": f"{city.name}, {city.region}",
                "data": {
                    "city": city.name,
                    "region": city.region,
                    "city_with_type": f"г {city.name}",
                    "region_with_type": f"{city.region}"
                }
            })
        
        return Response({"suggestions": suggestions})
    
    # Используем Dadata API
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {api_key}"
    }
    
    data = {
        "query": query,
        "count": 10,
        "locations": [{"country": "*"}],
        "from_bound": {"value": "city"},
        "to_bound": {"value": "city"}
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        return Response(result)
    
    except requests.exceptions.RequestException as e:
        # При ошибке API возвращаем данные из локальной БД
        cities = City.objects.filter(
            Q(name__icontains=query)
        )[:10]
        
        suggestions = []
        for city in cities:
            suggestions.append({
                "value": f"{city.name}, {city.region}",
                "data": {
                    "city": city.name,
                    "region": city.region
                }
            })
        
        return Response({"suggestions": suggestions})
