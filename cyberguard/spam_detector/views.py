"""
Views for the spam_detector app + shared home/history pages.
"""

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import csv

from .forms import SMSForm
from .models import PredictionLog
from .ml_utils import predict_sms


# ── Helper ────────────────────────────────────────────────────────────────────
def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ── Home Page ─────────────────────────────────────────────────────────────────
def home(request):
    """Landing page with project overview and statistics."""
    total = PredictionLog.objects.count()
    sms_count = PredictionLog.objects.filter(type='SMS').count()
    url_count = PredictionLog.objects.filter(type='URL').count()
    threat_count = PredictionLog.objects.filter(
        prediction__in=['Spam', 'Malicious']
    ).count()

    context = {
        'total_predictions': total,
        'sms_predictions': sms_count,
        'url_predictions': url_count,
        'threat_count': threat_count,
        'recent': PredictionLog.objects.all()[:5],
    }
    return render(request, 'home.html', context)


# ── SMS Checker ───────────────────────────────────────────────────────────────
def sms_checker(request):
    """SMS spam detection page."""
    form = SMSForm()
    result = None
    error = None

    if request.method == 'POST':
        form = SMSForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['message']
            try:
                result = predict_sms(text)
                # Log to database
                PredictionLog.objects.create(
                    input_text=text[:500],
                    prediction=result['prediction'],
                    confidence=result['confidence'],
                    type='SMS',
                    ip_address=get_client_ip(request),
                )
            except RuntimeError as e:
                error = str(e)

    context = {
        'form': form,
        'result': result,
        'error': error,
        'page': 'sms',
    }
    return render(request, 'spam_detector/sms_checker.html', context)


# ── History Page ──────────────────────────────────────────────────────────────
def history(request):
    """Paginated prediction history table."""
    filter_type = request.GET.get('type', 'ALL')
    filter_result = request.GET.get('result', 'ALL')

    logs = PredictionLog.objects.all()

    if filter_type in ('SMS', 'URL'):
        logs = logs.filter(type=filter_type)
    if filter_result == 'THREAT':
        logs = logs.filter(prediction__in=['Spam', 'Malicious'])
    elif filter_result == 'SAFE':
        logs = logs.filter(prediction__in=['Not Spam', 'Safe'])

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'filter_result': filter_result,
        'total_count': logs.count(),
        'page': 'history',
    }
    return render(request, 'history.html', context)


# ── CSV Export ────────────────────────────────────────────────────────────────
def export_history_csv(request):
    """Download full prediction history as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cyberguard_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Type', 'Input', 'Prediction', 'Confidence (%)', 'Timestamp'])

    for log in PredictionLog.objects.all():
        writer.writerow([
            log.id,
            log.type,
            log.input_text[:100],
            log.prediction,
            f"{log.confidence * 100:.1f}",
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response


# ── AJAX endpoint ─────────────────────────────────────────────────────────────
def sms_predict_ajax(request):
    """AJAX endpoint for real-time SMS prediction (no page reload)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
        text = body.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        text = request.POST.get('message', '').strip()

    if not text or len(text) < 3:
        return JsonResponse({'error': 'Message too short'}, status=400)

    try:
        result = predict_sms(text)
        PredictionLog.objects.create(
            input_text=text[:500],
            prediction=result['prediction'],
            confidence=result['confidence'],
            type='SMS',
            ip_address=get_client_ip(request),
        )
        return JsonResponse(result)
    except RuntimeError as e:
        return JsonResponse({'error': str(e)}, status=500)
