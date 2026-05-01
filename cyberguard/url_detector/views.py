"""
Views for the url_detector app.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse

from .forms import URLForm
from .ml_utils import predict_url
from spam_detector.models import PredictionLog


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def url_checker(request):
    """URL malicious classification page."""
    form = URLForm()
    result = None
    error = None

    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            try:
                result = predict_url(url)
                PredictionLog.objects.create(
                    input_text=url[:500],
                    prediction=result['prediction'],
                    confidence=result['confidence'],
                    type='URL',
                    ip_address=get_client_ip(request),
                )
            except RuntimeError as e:
                error = str(e)

    context = {
        'form': form,
        'result': result,
        'error': error,
        'page': 'url',
    }
    return render(request, 'url_detector/url_checker.html', context)


def url_predict_ajax(request):
    """AJAX endpoint for real-time URL prediction."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
        url = body.get('url', '').strip()
    except (json.JSONDecodeError, AttributeError):
        url = request.POST.get('url', '').strip()

    if not url or len(url) < 4:
        return JsonResponse({'error': 'URL too short'}, status=400)

    try:
        result = predict_url(url)
        PredictionLog.objects.create(
            input_text=url[:500],
            prediction=result['prediction'],
            confidence=result['confidence'],
            type='URL',
            ip_address=get_client_ip(request),
        )
        return JsonResponse(result)
    except RuntimeError as e:
        return JsonResponse({'error': str(e)}, status=500)
