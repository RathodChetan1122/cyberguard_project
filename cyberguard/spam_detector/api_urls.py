from django.urls import path
from . import api_views

urlpatterns = [
    path('sms/predict/', api_views.SMSPredictAPIView.as_view(), name='api_sms_predict'),
    path('history/', api_views.PredictionHistoryAPIView.as_view(), name='api_history'),
]
