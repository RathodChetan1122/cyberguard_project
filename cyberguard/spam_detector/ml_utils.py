"""
ML Utility functions for SMS Spam Detection.
Loads pre-trained model and vectorizer, performs predictions.
"""

import os
import re
import string
import joblib
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Model paths ──────────────────────────────────────────────────────────────
MODELS_DIR = getattr(settings, 'ML_MODELS_DIR', Path(settings.BASE_DIR) / 'ml_models')
SMS_MODEL_PATH = MODELS_DIR / 'sms_model.pkl'
SMS_VECTORIZER_PATH = MODELS_DIR / 'sms_vectorizer.pkl'

# ── Cached model objects (loaded once) ───────────────────────────────────────
_sms_model = None
_sms_vectorizer = None

# ── Suspicious keyword list (for UI highlighting) ────────────────────────────
SUSPICIOUS_WORDS = [
    'free', 'win', 'winner', 'won', 'prize', 'cash', 'claim', 'urgent',
    'call now', 'limited', 'offer', 'click', 'link', 'verify', 'account',
    'password', 'bank', 'credit', 'loan', 'money', 'reward', 'bonus',
    'congratulations', 'selected', 'discount', 'deal', 'guaranteed',
    'risk-free', 'act now', 'expire', 'exclusive', 'dear friend',
    'million', 'billion', 'investment', 'nigeria', 'inheritance',
]


def _load_sms_models():
    """Lazy-load SMS model and vectorizer from disk."""
    global _sms_model, _sms_vectorizer
    if _sms_model is None or _sms_vectorizer is None:
        try:
            _sms_model = joblib.load(SMS_MODEL_PATH)
            _sms_vectorizer = joblib.load(SMS_VECTORIZER_PATH)
            logger.info("SMS model and vectorizer loaded successfully.")
        except FileNotFoundError:
            logger.error(
                "SMS model files not found. Run: python ml_training/train_sms_model.py"
            )
            raise RuntimeError(
                "SMS model not found. Please run the training script first: "
                "python ml_training/train_sms_model.py"
            )
    return _sms_model, _sms_vectorizer


def preprocess_text(text: str) -> str:
    """
    Clean and normalize raw SMS text.
    Steps: lowercase → remove punctuation → collapse whitespace.
    (Stopword removal is baked into the TF-IDF vectorizer via its params.)
    """
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', ' url ', text)   # replace URLs
    text = re.sub(r'\d+', ' num ', text)               # replace numbers
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def highlight_suspicious_words(text: str) -> str:
    """
    Wrap suspicious words in <mark> tags for UI highlighting.
    Returns HTML-safe string.
    """
    import html
    safe_text = html.escape(text)
    for word in sorted(SUSPICIOUS_WORDS, key=len, reverse=True):
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        safe_text = pattern.sub(
            lambda m: f'<mark class="suspicious-word">{m.group()}</mark>',
            safe_text
        )
    return safe_text


def predict_sms(text: str) -> dict:
    """
    Predict whether an SMS is Spam or Not Spam.

    Args:
        text: Raw SMS message string.

    Returns:
        dict with keys:
            prediction (str): 'Spam' or 'Not Spam'
            confidence (float): 0.0–1.0
            confidence_percent (str): e.g. '94.3%'
            highlighted_text (str): HTML with suspicious words marked
            suspicious_words_found (list): list of matched suspicious words
            preprocessed (str): cleaned text fed to model
    """
    model, vectorizer = _load_sms_models()

    cleaned = preprocess_text(text)
    features = vectorizer.transform([cleaned])
    prediction_idx = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]

    # Label mapping: model trained with 0=ham, 1=spam
    label = 'Spam' if prediction_idx == 1 else 'Not Spam'
    confidence = float(probabilities[prediction_idx])

    # Find suspicious words in original text
    text_lower = text.lower()
    found_suspicious = [w for w in SUSPICIOUS_WORDS if w in text_lower]

    return {
        'prediction': label,
        'confidence': confidence,
        'confidence_percent': f"{confidence * 100:.1f}%",
        'highlighted_text': highlight_suspicious_words(text),
        'suspicious_words_found': found_suspicious,
        'preprocessed': cleaned,
        'is_spam': label == 'Spam',
    }
