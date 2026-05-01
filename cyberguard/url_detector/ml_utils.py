"""
ML Utility functions for Malicious URL Classification.
Extracts hand-crafted features from URLs and runs Random Forest prediction.
"""

import re
import os
import math
import joblib
import logging
from pathlib import Path
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Model paths ───────────────────────────────────────────────────────────────
MODELS_DIR = getattr(settings, 'ML_MODELS_DIR', Path(settings.BASE_DIR) / 'ml_models')
URL_MODEL_PATH = MODELS_DIR / 'url_model.pkl'

# ── Cached model ──────────────────────────────────────────────────────────────
_url_model = None

# ── Suspicious keywords ───────────────────────────────────────────────────────
SUSPICIOUS_KEYWORDS = [
    'login', 'signin', 'sign-in', 'bank', 'verify', 'verification',
    'update', 'secure', 'security', 'account', 'password', 'credential',
    'free', 'win', 'winner', 'prize', 'claim', 'reward', 'bonus',
    'click', 'here', 'urgent', 'alert', 'confirm', 'paypal', 'ebay',
    'amazon', 'apple', 'google', 'microsoft', 'support', 'helpdesk',
    'billing', 'invoice', 'payment', 'transfer', 'wire', 'crypto',
    'bitcoin', '0ffice', '0nline', 'auth', 'validate', 'activation',
]

BENIGN_TLDS = {'.com', '.org', '.net', '.edu', '.gov', '.io', '.co'}
SUSPICIOUS_TLDS = {'.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top',
                   '.pw', '.ru', '.cn', '.info', '.biz', '.cc'}


def _load_url_model():
    """Lazy-load URL classification model from disk."""
    global _url_model
    if _url_model is None:
        try:
            _url_model = joblib.load(URL_MODEL_PATH)
            logger.info("URL model loaded successfully.")
        except FileNotFoundError:
            logger.error(
                "URL model not found. Run: python ml_training/train_url_model.py"
            )
            raise RuntimeError(
                "URL model not found. Please run: python ml_training/train_url_model.py"
            )
    return _url_model


def extract_url_features(url: str) -> dict:
    """
    Extract a rich set of lexical/structural features from a URL.
    Returns both a feature dict (for display) and a flat list (for the model).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        parsed = urlparse('http://unknown')

    full_url   = url.lower()
    scheme     = parsed.scheme.lower()
    netloc     = parsed.netloc.lower()
    path       = parsed.path.lower()
    query      = parsed.query.lower()
    domain     = netloc.replace('www.', '')

    # ── Basic counts ──────────────────────────────────────────────────────────
    url_length          = len(url)
    dot_count           = url.count('.')
    hyphen_count        = url.count('-')
    underscore_count    = url.count('_')
    slash_count         = url.count('/')
    at_symbol           = 1 if '@' in url else 0
    digit_count         = sum(c.isdigit() for c in url)
    special_char_count  = sum(1 for c in url if not c.isalnum() and c not in ('/', '.', ':'))
    subdomain_count     = max(0, netloc.count('.') - 1)
    query_param_count   = len(query.split('&')) if query else 0
    path_depth          = len([p for p in path.split('/') if p])

    # ── Boolean flags ──────────────────────────────────────────────────────────
    uses_https          = 1 if scheme == 'https' else 0
    has_ip_address      = 1 if re.match(r'\d+\.\d+\.\d+\.\d+', netloc) else 0
    has_port            = 1 if ':' in netloc and not netloc.endswith(':443') and not netloc.endswith(':80') else 0
    double_slash        = 1 if '//' in path else 0
    has_redirect        = 1 if url.count('http') > 1 else 0

    # ── Keyword flags ─────────────────────────────────────────────────────────
    keyword_count       = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in full_url)
    found_keywords      = [kw for kw in SUSPICIOUS_KEYWORDS if kw in full_url]

    # ── TLD analysis ──────────────────────────────────────────────────────────
    tld = ''
    parts = domain.split('.')
    if len(parts) >= 2:
        tld = '.' + parts[-1]
    suspicious_tld      = 1 if tld in SUSPICIOUS_TLDS else 0

    # ── Entropy (randomness of domain name) ──────────────────────────────────
    def shannon_entropy(s):
        if not s:
            return 0.0
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        return -sum((f / len(s)) * math.log2(f / len(s)) for f in freq.values())

    domain_entropy      = round(shannon_entropy(domain.split('.')[0] if '.' in domain else domain), 3)
    domain_length       = len(domain)

    # ── Assemble feature vector (must match training order) ──────────────────
    feature_vector = [
        url_length,
        dot_count,
        hyphen_count,
        underscore_count,
        slash_count,
        at_symbol,
        digit_count,
        special_char_count,
        subdomain_count,
        query_param_count,
        path_depth,
        uses_https,
        has_ip_address,
        has_port,
        double_slash,
        has_redirect,
        keyword_count,
        suspicious_tld,
        domain_entropy,
        domain_length,
    ]

    feature_display = {
        'URL Length':           url_length,
        'Dot Count':            dot_count,
        'Hyphen Count':         hyphen_count,
        'Digit Count':          digit_count,
        'Uses HTTPS':           bool(uses_https),
        'Has @ Symbol':         bool(at_symbol),
        'Has IP Address':       bool(has_ip_address),
        'Subdomain Count':      subdomain_count,
        'Suspicious Keywords':  keyword_count,
        'Suspicious TLD':       bool(suspicious_tld),
        'Domain Entropy':       domain_entropy,
        'Has Redirect':         bool(has_redirect),
    }

    return {
        'vector': feature_vector,
        'display': feature_display,
        'found_keywords': found_keywords,
        'domain': domain,
        'scheme': scheme,
        'tld': tld,
    }


def predict_url(url: str) -> dict:
    """
    Predict whether a URL is Malicious or Safe.

    Args:
        url: Raw URL string.

    Returns:
        dict with:
            prediction (str): 'Malicious' or 'Safe'
            confidence (float): 0.0–1.0
            risk_score (float): 0–100
            risk_level (str): 'Low' / 'Medium' / 'High' / 'Critical'
            features (dict): feature breakdown for display
            found_keywords (list): suspicious keywords found
    """
    model = _load_url_model()

    features = extract_url_features(url)
    vector = [features['vector']]

    prediction_idx = model.predict(vector)[0]
    probabilities  = model.predict_proba(vector)[0]

    label      = 'Malicious' if prediction_idx == 1 else 'Safe'
    confidence = float(probabilities[prediction_idx])
    risk_score = round(float(probabilities[1]) * 100, 1)   # prob of being malicious

    if risk_score < 25:
        risk_level = 'Low'
    elif risk_score < 50:
        risk_level = 'Medium'
    elif risk_score < 75:
        risk_level = 'High'
    else:
        risk_level = 'Critical'

    return {
        'prediction':        label,
        'confidence':        confidence,
        'confidence_percent': f"{confidence * 100:.1f}%",
        'risk_score':        risk_score,
        'risk_level':        risk_level,
        'features':          features['display'],
        'found_keywords':    features['found_keywords'],
        'domain':            features['domain'],
        'scheme':            features['scheme'],
        'is_malicious':      label == 'Malicious',
    }
