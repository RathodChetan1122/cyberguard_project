#!/usr/bin/env python
"""
train_url_model.py
==================
Train a Random Forest malicious URL classifier using hand-crafted features.

Dataset: Generates a synthetic-but-realistic training set based on common
         patterns of malicious vs benign URLs, then optionally enriches with
         any local CSV you supply (columns: url, label  where label in 0/1
         or 'benign'/'malicious').

Outputs (saved to ml_models/):
  - url_model.pkl       : Trained RandomForestClassifier
  - url_model_meta.txt  : Accuracy, feature importance
"""

import os
import re
import sys
import math
import random
import string
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse

# ── Paths ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODELS_DIR  = PROJECT_DIR / 'ml_models'
DATA_DIR    = SCRIPT_DIR / 'data'

MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ── Imports ───────────────────────────────────────────────────────────────
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        classification_report, accuracy_score, roc_auc_score, confusion_matrix
    )
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("ERROR: scikit-learn not found. Run: pip install scikit-learn pandas numpy")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION (must match url_detector/ml_utils.py)
# ════════════════════════════════════════════════════════════════════════════

SUSPICIOUS_KEYWORDS = [
    'login', 'signin', 'sign-in', 'bank', 'verify', 'verification',
    'update', 'secure', 'security', 'account', 'password', 'credential',
    'free', 'win', 'winner', 'prize', 'claim', 'reward', 'bonus',
    'click', 'here', 'urgent', 'alert', 'confirm', 'paypal', 'ebay',
    'amazon', 'apple', 'google', 'microsoft', 'support', 'helpdesk',
    'billing', 'invoice', 'payment', 'transfer', 'wire', 'crypto',
    'bitcoin', '0ffice', '0nline', 'auth', 'validate', 'activation',
]

SUSPICIOUS_TLDS = {'.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top',
                   '.pw', '.ru', '.cn', '.info', '.biz', '.cc'}

FEATURE_NAMES = [
    'url_length', 'dot_count', 'hyphen_count', 'underscore_count',
    'slash_count', 'at_symbol', 'digit_count', 'special_char_count',
    'subdomain_count', 'query_param_count', 'path_depth',
    'uses_https', 'has_ip_address', 'has_port', 'double_slash',
    'has_redirect', 'keyword_count', 'suspicious_tld',
    'domain_entropy', 'domain_length',
]


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    return -sum((f / len(s)) * math.log2(f / len(s)) for f in freq.values())


def extract_features(url: str) -> list:
    """Extract 20 features from a URL. Must stay in sync with ml_utils.py."""
    try:
        parsed = urlparse(url if '://' in url else 'http://' + url)
    except Exception:
        parsed = urlparse('http://unknown')

    full_url   = url.lower()
    scheme     = parsed.scheme.lower()
    netloc     = parsed.netloc.lower()
    path       = parsed.path.lower()
    query      = parsed.query.lower()
    domain     = netloc.replace('www.', '')

    url_length         = len(url)
    dot_count          = url.count('.')
    hyphen_count       = url.count('-')
    underscore_count   = url.count('_')
    slash_count        = url.count('/')
    at_symbol          = 1 if '@' in url else 0
    digit_count        = sum(c.isdigit() for c in url)
    special_char_count = sum(1 for c in url if not c.isalnum() and c not in ('/', '.', ':'))
    subdomain_count    = max(0, netloc.count('.') - 1)
    query_param_count  = len(query.split('&')) if query else 0
    path_depth         = len([p for p in path.split('/') if p])
    uses_https         = 1 if scheme == 'https' else 0
    has_ip_address     = 1 if re.match(r'\d+\.\d+\.\d+\.\d+', netloc) else 0
    has_port           = 1 if ':' in netloc and not netloc.endswith((':443', ':80')) else 0
    double_slash       = 1 if '//' in path else 0
    has_redirect       = 1 if url.count('http') > 1 else 0
    keyword_count      = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in full_url)

    tld = ''
    parts = domain.split('.')
    if len(parts) >= 2:
        tld = '.' + parts[-1]
    suspicious_tld = 1 if tld in SUSPICIOUS_TLDS else 0

    domain_name   = parts[0] if parts else ''
    domain_entropy = round(shannon_entropy(domain_name), 3)
    domain_length  = len(domain)

    return [
        url_length, dot_count, hyphen_count, underscore_count,
        slash_count, at_symbol, digit_count, special_char_count,
        subdomain_count, query_param_count, path_depth,
        uses_https, has_ip_address, has_port, double_slash,
        has_redirect, keyword_count, suspicious_tld,
        domain_entropy, domain_length,
    ]


# ════════════════════════════════════════════════════════════════════════════
# DATASET GENERATION
# ════════════════════════════════════════════════════════════════════════════

BENIGN_URLS = [
    "https://www.google.com/search?q=python+tutorial",
    "https://www.wikipedia.org/wiki/Machine_learning",
    "https://github.com/django/django",
    "https://stackoverflow.com/questions/tagged/python",
    "https://docs.python.org/3/library/os.html",
    "https://www.bbc.co.uk/news/technology",
    "https://www.amazon.com/dp/B08N5WRWNW",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.reddit.com/r/programming",
    "https://medium.com/@author/machine-learning-intro",
    "https://arxiv.org/abs/2301.00001",
    "https://en.wikipedia.org/wiki/Cybersecurity",
    "https://www.microsoft.com/en-us/security",
    "https://developer.mozilla.org/en-US/docs/Web",
    "https://www.cloudflare.com/learning/ddos/what-is-a-ddos-attack",
    "https://www.kaggle.com/datasets",
    "https://pypi.org/project/scikit-learn/",
    "https://www.coursera.org/learn/machine-learning",
    "https://news.ycombinator.com/item?id=12345",
    "https://www.linkedin.com/in/username",
    "https://twitter.com/username/status/123",
    "https://www.netflix.com/title/80057281",
    "https://maps.google.com/maps?q=london",
    "https://www.nhs.uk/conditions/coronavirus-covid-19",
    "http://www.bbc.com/sport/football",
    "https://mail.google.com/mail/u/0/#inbox",
    "https://drive.google.com/file/d/abc123/view",
    "https://outlook.office365.com/mail",
    "https://www.apple.com/iphone",
    "https://en.m.wikipedia.org/wiki/Python_(programming_language)",
] * 20  # 600 benign

MALICIOUS_URLS = [
    "http://secure-login-paypal.tk/verify?user=admin&token=x7a",
    "http://www.amazon-prize-claim.ml/win/free-iphone",
    "http://192.168.1.1/admin/login.php",
    "http://update-your-account.gq/banking/login",
    "http://free-gift-card-amazon.xyz/claim/500",
    "http://paypal-account-verify.cf/secure/update",
    "http://login-security-apple.tk/appleid/verification",
    "http://ebay-seller-support.ml/resolution/case",
    "http://bit.ly/3xFreeIphone14ProMax",
    "http://tiny.cc/winprize2024",
    "http://bank-secure-login.ru/account/password-reset",
    "http://microsoft-helpdesk-support.xyz/windows/activation",
    "http://click-here-to-win.biz/prize/claim?id=99871",
    "http://verify-your-credentials.pw/signin/confirm",
    "http://crypto-investment-doubler.top/bitcoin/double",
    "http://www.faceb00k-login.com/checkpoint/security",
    "http://g00gle-security-alert.tk/account/verify",
    "http://amazon-order-1234567.ml/track/package",
    "http://instagram-account-suspended.gq/unblock",
    "http://netflix-payment-failed.xyz/update/billing",
    "http://10.0.0.1:8080/admin/phpmyadmin",
    "http://172.16.254.1/setup/login.html",
    "http://urgent-bank-notification.info/login",
    "http://claim-your-reward-now.cc/prize/500-gift",
    "http://secure-update-required.biz/account/update",
    "http://apple-id-suspended.ml/recovery/unlock",
    "http://support-microsoft-windows.tk/activate/license",
    "http://account-suspended-verify.cf/reactivate",
    "http://free-antivirus-download.top/setup.exe",
    "http://lottery-winner-2024.gq/claim/prize",
    "http://paypal.com.account-secure.tk/login",
    "http://www.amazon.de.order-status.ml/track",
    "http://secure.bank-validation.xyz/auth/login",
    "http://ebay.com.seller-case-123.cf/resolve",
    "http://apple-support-case.gq/verify-identity",
    "http://microsoft365-activation.tk/product-key",
    "http://gmail-suspicious-login.ml/verify/account",
    "http://instagram-verify.cf/confirm-account",
    "http://whatsapp-account-expired.top/renew",
    "http://netflix-subscription.biz/update-payment",
] * 15  # 600 malicious

# Extra patterns with varied structure
def generate_malicious_url():
    """Generate a synthetic malicious URL with realistic patterns."""
    domains = [
        'paypal', 'amazon', 'apple', 'google', 'microsoft',
        'bank', 'secure', 'account', 'login', 'verify'
    ]
    tlds = ['.tk', '.ml', '.gq', '.cf', '.xyz', '.top', '.ru', '.cn', '.pw']
    paths = [
        '/verify', '/login', '/account/update', '/secure/confirm',
        '/claim/prize', '/win/reward', '/admin/access', '/reset/password',
        '/activation/key', '/validate/credential', '/update/billing'
    ]
    queries = [
        '?token=abc123&id=9999',
        '?user=admin&session=x7k',
        '?redirect=http://real-site.com',
        '?confirm=true&code=AA1234',
        '',
    ]
    scheme = random.choice(['http://', 'http://'])  # malicious rarely use https
    domain = random.choice(domains)
    suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
    tld = random.choice(tlds)
    path = random.choice(paths)
    query = random.choice(queries)
    return f"{scheme}{domain}-{suffix}{tld}{path}{query}"


def generate_benign_url():
    """Generate a synthetic benign URL."""
    domains = ['news', 'blog', 'shop', 'info', 'docs', 'api', 'support', 'help']
    companies = ['github', 'gitlab', 'heroku', 'vercel', 'netlify', 'cloudflare']
    tlds = ['.com', '.org', '.net', '.io', '.co.uk', '.edu']
    paths = [
        '/about', '/products', '/blog/post-title', '/docs/getting-started',
        '/api/v2/users', '/contact', '/pricing', '/features', ''
    ]
    subdomain = random.choice(['www.', 'docs.', 'api.', 'blog.', ''])
    base = random.choice(companies + domains)
    suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 6)))
    tld = random.choice(tlds)
    path = random.choice(paths)
    return f"https://{subdomain}{base}{suffix}{tld}{path}"


def load_dataset():
    """Build the training dataset."""
    # Check for user-supplied dataset
    local_csv = DATA_DIR / 'url_dataset.csv'
    urls, labels = [], []

    if local_csv.exists():
        print(f"  Found local URL dataset: {local_csv}")
        try:
            df_user = pd.read_csv(str(local_csv))
            # Try common column name patterns
            for url_col in ['url', 'URL', 'Url']:
                for lbl_col in ['label', 'Label', 'type', 'Type', 'class', 'Class']:
                    if url_col in df_user.columns and lbl_col in df_user.columns:
                        df_sub = df_user[[url_col, lbl_col]].dropna()
                        # Normalise labels
                        df_sub[lbl_col] = df_sub[lbl_col].astype(str).str.lower()
                        df_sub['enc'] = df_sub[lbl_col].map(
                            lambda x: 1 if x in ('malicious', 'phishing', 'spam', 'bad', '1') else 0
                        )
                        urls   += df_sub[url_col].tolist()
                        labels += df_sub['enc'].tolist()
                        print(f"  Loaded {len(df_sub)} rows from user CSV.")
                        break
        except Exception as e:
            print(f"  Could not read user CSV ({e}), using built-in dataset.")

    # Add built-in samples
    all_malicious = MALICIOUS_URLS + [generate_malicious_url() for _ in range(200)]
    all_benign    = BENIGN_URLS    + [generate_benign_url()    for _ in range(200)]

    urls   += all_malicious + all_benign
    labels += [1] * len(all_malicious) + [0] * len(all_benign)

    df = pd.DataFrame({'url': urls, 'label': labels})
    df.drop_duplicates(subset='url', inplace=True)
    return df


# ════════════════════════════════════════════════════════════════════════════
# TRAINING
# ════════════════════════════════════════════════════════════════════════════

def train():
    print("\n" + "═" * 60)
    print("   CyberGuard — URL Threat Model Training")
    print("═" * 60 + "\n")

    # ── Load data ──────────────────────────────────────────────────────────
    print("[1/5] Loading URL dataset…")
    df = load_dataset()
    print(f"  Total URLs    : {len(df)}")
    print(f"  Malicious (1) : {(df['label'] == 1).sum()}")
    print(f"  Benign    (0) : {(df['label'] == 0).sum()}")

    # ── Extract features ───────────────────────────────────────────────────
    print("\n[2/5] Extracting features…")
    feature_rows = [extract_features(url) for url in df['url']]
    X = np.array(feature_rows, dtype=float)
    y = df['label'].values
    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Features: {', '.join(FEATURE_NAMES)}")

    # ── Split ──────────────────────────────────────────────────────────────
    print("\n[3/5] Splitting data (80/20)…")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

    # ── Train ──────────────────────────────────────────────────────────────
    print("\n[4/5] Training Random Forest Classifier…")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,
        class_weight='balanced',
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc   = accuracy_score(y_test, preds)
    auc   = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

    print(f"  Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"  ROC-AUC  : {auc:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, preds, target_names=['Benign', 'Malicious']))

    # Feature importance
    print("  Top-10 Feature Importances:")
    importance = list(zip(FEATURE_NAMES, model.feature_importances_))
    importance.sort(key=lambda x: x[1], reverse=True)
    for name, imp in importance[:10]:
        bar = '█' * int(imp * 50)
        print(f"    {name:<25} {imp:.4f}  {bar}")

    # ── Save ──────────────────────────────────────────────────────────────
    print("\n[5/5] Saving model…")
    model_path = MODELS_DIR / 'url_model.pkl'
    joblib.dump(model, str(model_path))
    print(f"  ✓ Saved: {model_path}")

    meta_path = MODELS_DIR / 'url_model_meta.txt'
    meta_path.write_text(
        f"Model: RandomForestClassifier\n"
        f"Accuracy: {acc*100:.2f}%\n"
        f"ROC-AUC:  {auc*100:.2f}%\n"
        f"Train size: {len(X_train)}\n"
        f"Test size:  {len(X_test)}\n"
        f"N-estimators: 150\n"
        f"\nFeature Importances:\n" +
        '\n'.join(f"  {n}: {v:.4f}" for n, v in importance)
    )

    print("\n" + "═" * 60)
    print(f"  ✅ URL Model Training Complete!")
    print(f"  Final Accuracy: {acc*100:.2f}%  |  AUC: {auc*100:.2f}%")
    print("═" * 60 + "\n")


if __name__ == '__main__':
    sys.path.insert(0, str(PROJECT_DIR))
    train()
