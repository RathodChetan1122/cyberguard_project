# CyberGuard — AI SMS Spam & Malicious URL Detection System

A production-ready Django web application with dual ML modules for detecting
SMS spam and malicious URLs using scikit-learn.

---

## 📁 Project Structure

```
cyberguard/
├── cyberguard/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── spam_detector/           # SMS spam detection app
│   ├── models.py            # PredictionLog DB model
│   ├── views.py
│   ├── forms.py
│   ├── ml_utils.py          # predict_sms()
│   ├── urls.py
│   ├── api_urls.py          # REST API endpoints
│   └── api_views.py
├── url_detector/            # Malicious URL detection app
│   ├── views.py
│   ├── forms.py
│   ├── ml_utils.py          # predict_url()
│   ├── urls.py
│   ├── api_urls.py
│   └── api_views.py
├── templates/               # All HTML templates
│   ├── base.html
│   ├── home.html
│   ├── history.html
│   ├── spam_detector/
│   │   └── sms_checker.html
│   └── url_detector/
│       └── url_checker.html
├── static/
│   ├── css/cyberguard.css
│   └── js/cyberguard.js
├── ml_training/
│   ├── train_sms_model.py   # SMS model training script
│   ├── train_url_model.py   # URL model training script
│   └── data/                # Place datasets here
├── ml_models/               # Auto-created; stores .pkl files
├── manage.py
├── setup_models.py          # One-command model training
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Train ML Models

```bash
# One command trains both models:
python setup_models.py
```

This will:
- Auto-download the UCI SMS Spam dataset (or use built-in samples)
- Generate URL training data
- Save `ml_models/sms_model.pkl`, `sms_vectorizer.pkl`, `url_model.pkl`

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create Admin User

```bash
python manage.py createsuperuser
```

### 6. Start the Server

```bash
python manage.py runserver
```

Open in browser: **http://127.0.0.1:8000**

---

## 🌐 Pages

| URL | Description |
|-----|-------------|
| `/` | Home — stats, module overview |
| `/sms/` | SMS Spam Checker |
| `/url/` | URL Threat Scanner |
| `/sms/history/` | Prediction history table |
| `/admin/` | Django admin panel |

---

## 🔌 REST API

### Predict SMS Spam

```bash
POST /api/sms/predict/
Content-Type: application/json

{"message": "Congratulations! You won a free iPhone!"}
```

Response:
```json
{
  "prediction": "Spam",
  "confidence": 0.982,
  "confidence_percent": "98.2%",
  "is_spam": true,
  "suspicious_words": ["congratulations", "free", "won"]
}
```

### Predict URL

```bash
POST /api/url/predict/
Content-Type: application/json

{"url": "http://paypal-verify.tk/login"}
```

Response:
```json
{
  "prediction": "Malicious",
  "confidence": 0.944,
  "risk_score": 94.4,
  "risk_level": "Critical",
  "is_malicious": true,
  "found_keywords": ["paypal", "verify", "login"],
  "domain": "paypal-verify.tk"
}
```

### Get History

```bash
GET /api/history/
```

---

## 🧠 ML Models

### Module 1: SMS Spam Detection

| Component | Choice |
|-----------|--------|
| Algorithm | Multinomial Naive Bayes |
| Features | TF-IDF (unigrams + bigrams, 8000 vocab) |
| Dataset | UCI SMS Spam Collection (~5,574 messages) |
| Accuracy | ~98%+ on full dataset |

Preprocessing pipeline:
1. Lowercase
2. Replace URLs → `url`
3. Replace numbers → `num`
4. Remove punctuation
5. Remove stopwords
6. TF-IDF vectorisation

### Module 2: Malicious URL Classification

| Component | Choice |
|-----------|--------|
| Algorithm | Random Forest (150 trees) |
| Features | 20 lexical/structural features |
| Dataset | Synthetic + optional user-supplied CSV |

Feature list:
- URL length, dot count, hyphen count, underscore count
- Slash count, @ symbol, digit count, special char count
- Subdomain count, query param count, path depth
- HTTPS usage, IP address, port, double slash, redirect
- Suspicious keyword count, suspicious TLD
- Domain entropy (Shannon), domain length

---

## 📊 Using Your Own Datasets

### SMS Dataset
Place `SMSSpamCollection` (tab-separated TSV) in `ml_training/data/`:
```
ham     Go until jurong point, crazy.. Available only in bugis...
spam    Free entry in 2 a wkly comp to win FA Cup final tkts...
```

### URL Dataset
Place `url_dataset.csv` in `ml_training/data/`:
```csv
url,label
https://www.google.com,0
http://phish-paypal.tk/login,1
```
Label: `0` = benign, `1` = malicious

---

## ⚙️ Admin Panel

Visit `/admin/` to:
- View all prediction logs
- Filter by type (SMS/URL) and result
- Delete entries

---

## 📦 Export History

Download all predictions as CSV:
```
GET /sms/history/export/
```

---

## 🔧 Troubleshooting

**"SMS model not found"**
→ Run `python setup_models.py`

**Import errors**
→ Ensure venv is activated: `source venv/bin/activate`

**Database errors**
→ Run `python manage.py migrate`

**Port already in use**
→ `python manage.py runserver 8080`
