from django.contrib import admin
from .models import PredictionLog


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ('type', 'prediction', 'confidence_percent', 'timestamp', 'ip_address')
    list_filter = ('type', 'prediction', 'timestamp')
    search_fields = ('input_text', 'prediction')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
