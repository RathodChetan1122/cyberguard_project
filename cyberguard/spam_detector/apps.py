from django.apps import AppConfig


class SpamDetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spam_detector'
    verbose_name = 'SMS Spam Detector'
