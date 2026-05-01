"""
REST API views using Django REST Framework.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PredictionLog
from .ml_utils import predict_sms


class SMSPredictAPIView(APIView):
    """
    POST /api/sms/predict/
    Body: {"message": "Your SMS text here"}
    Returns prediction result.
    """

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message or len(message) < 3:
            return Response(
                {'error': 'Message must be at least 3 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            result = predict_sms(message)
            PredictionLog.objects.create(
                input_text=message[:500],
                prediction=result['prediction'],
                confidence=result['confidence'],
                type='SMS',
            )
            return Response({
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'confidence_percent': result['confidence_percent'],
                'is_spam': result['is_spam'],
                'suspicious_words': result['suspicious_words_found'],
            })
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PredictionHistoryAPIView(APIView):
    """
    GET /api/history/  — returns last 50 prediction logs as JSON.
    """

    def get(self, request):
        logs = PredictionLog.objects.all()[:50]
        data = [
            {
                'id': log.id,
                'type': log.type,
                'input': log.input_text[:80],
                'prediction': log.prediction,
                'confidence': log.confidence,
                'timestamp': log.timestamp.isoformat(),
            }
            for log in logs
        ]
        return Response({'count': len(data), 'results': data})
