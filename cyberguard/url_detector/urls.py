from django.urls import path
from . import views

urlpatterns = [
    path('', views.url_checker, name='url_checker'),
    path('predict/', views.url_predict_ajax, name='url_predict_ajax'),
]
