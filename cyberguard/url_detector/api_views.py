from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ml_utils import predict_url
from spam_detector.models import PredictionLog
import re


class URLPredictAPIView(APIView):
    """
    POST /api/url/predict/
    Body: {"url": "https://suspicious-site.tk/login"}
    """

    def post(self, request):
        url = request.data.get('url', '').strip()
        if not url or len(url) < 4:
            return Response(
                {'error': 'URL must be at least 4 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not re.match(r'^https?://', url, re.IGNORECASE):
            url = 'http://' + url

        try:
            result = predict_url(url)
            PredictionLog.objects.create(
                input_text=url[:500],
                prediction=result['prediction'],
                confidence=result['confidence'],
                type='URL',
            )
            return Response({
                'prediction':        result['prediction'],
                'confidence':        result['confidence'],
                'confidence_percent': result['confidence_percent'],
                'risk_score':        result['risk_score'],
                'risk_level':        result['risk_level'],
                'is_malicious':      result['is_malicious'],
                'found_keywords':    result['found_keywords'],
                'domain':            result['domain'],
            })
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
