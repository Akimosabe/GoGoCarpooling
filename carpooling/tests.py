from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status

class PingTestCase(APITestCase):
    def test_ping(self):
        response = self.client.get('/ping/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
