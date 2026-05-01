from django.db import models


class PredictionLog(models.Model):
    """Stores history of all predictions made by the system."""

    TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('URL', 'URL'),
    ]

    input_text = models.TextField(help_text="The raw input provided by the user")
    prediction = models.CharField(max_length=50, help_text="Spam/Not Spam or Malicious/Safe")
    confidence = models.FloatField(help_text="Confidence score (0.0 - 1.0)")
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, help_text="SMS or URL")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Prediction Log'
        verbose_name_plural = 'Prediction Logs'

    def __str__(self):
        return f"[{self.type}] {self.prediction} ({self.confidence:.1%}) — {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @property
    def confidence_percent(self):
        return f"{self.confidence * 100:.1f}%"

    @property
    def is_threat(self):
        return self.prediction in ('Spam', 'Malicious')
