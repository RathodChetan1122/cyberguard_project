from django.urls import path
from . import api_views

urlpatterns = [
    path('url/predict/', api_views.URLPredictAPIView.as_view(), name='api_url_predict'),
]
