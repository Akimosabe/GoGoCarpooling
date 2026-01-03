from rest_framework.views import APIView
from rest_framework.response import Response

#тестовый пинг

class PingAPIView(APIView):
    def get(self, request):
        return Response({
            "status": "ok",
            "message": "DRF is working"
        })
