"""
URL configuration for cyberguard project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from spam_detector import views as home_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_views.home, name='home'),
    path('sms/', include('spam_detector.urls')),
    path('url/', include('url_detector.urls')),
    # REST API
    path('api/', include('spam_detector.api_urls')),
    path('api/', include('url_detector.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
