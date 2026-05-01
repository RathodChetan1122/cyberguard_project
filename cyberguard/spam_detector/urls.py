from django.urls import path
from . import views

urlpatterns = [
    path('', views.sms_checker, name='sms_checker'),
    path('predict/', views.sms_predict_ajax, name='sms_predict_ajax'),
    path('history/', views.history, name='history'),
    path('history/export/', views.export_history_csv, name='export_history'),
]
