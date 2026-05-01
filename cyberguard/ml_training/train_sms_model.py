#!/usr/bin/env python
"""
train_sms_model.py
==================
Train a Multinomial Naive Bayes SMS spam classifier.

Dataset: UCI SMS Spam Collection
  - Auto-downloaded from UCI ML repo if not present locally.
  - Or place 'SMSSpamCollection' (tab-separated) in ml_training/ folder.

Outputs (saved to ml_models/):
  - sms_model.pkl       : Trained MultinomialNB classifier
  - sms_vectorizer.pkl  : Fitted TF-IDF vectorizer
"""

import os
import re
import sys
import string
import urllib.request
import zipfile
import io
import pickle
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODELS_DIR  = PROJECT_DIR / 'ml_models'
DATA_DIR    = SCRIPT_DIR / 'data'

MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ── Imports ───────────────────────────────────────────────────────────────
try:
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        classification_report, confusion_matrix,
        accuracy_score, roc_auc_score
    )
    from sklearn.pipeline import Pipeline
except ImportError:
    print("ERROR: scikit-learn not found. Run: pip install scikit-learn pandas numpy")
    sys.exit(1)

try:
    import nltk
    from nltk.corpus import stopwords
    try:
        STOPWORDS = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords', quiet=True)
        STOPWORDS = set(stopwords.words('english'))
except ImportError:
    STOPWORDS = set()
    print("Warning: nltk not installed, skipping stopword removal.")


# ════════════════════════════════════════════════════════════════════════════
# 1.  LOAD / DOWNLOAD DATASET
# ════════════════════════════════════════════════════════════════════════════

def load_dataset() -> pd.DataFrame:
    """
    Load the UCI SMS Spam Collection dataset.
    Tries local file first; falls back to UCI URL; final fallback: built-in samples.
    """
    local_paths = [
        DATA_DIR / 'SMSSpamCollection',
        SCRIPT_DIR / 'SMSSpamCollection',
        PROJECT_DIR / 'SMSSpamCollection',
        DATA_DIR / 'sms_spam.csv',
    ]

    for path in local_paths:
        if path.exists():
            print(f"  Loading dataset from: {path}")
            try:
                df = pd.read_csv(str(path), sep='\t', header=None,
                                 names=['label', 'message'], encoding='utf-8')
                print(f"  Loaded {len(df)} rows.")
                return df
            except Exception:
                try:
                    df = pd.read_csv(str(path), header=0, encoding='utf-8')
                    if 'label' in df.columns and 'message' in df.columns:
                        return df
                except Exception:
                    pass

    # Try downloading from UCI
    print("  Local dataset not found. Attempting download from UCI ML Repo…")
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            zip_data = response.read()
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            with z.open('SMSSpamCollection') as f:
                content = f.read().decode('utf-8')
        save_path = DATA_DIR / 'SMSSpamCollection'
        save_path.write_text(content, encoding='utf-8')
        df = pd.read_csv(str(save_path), sep='\t', header=None,
                         names=['label', 'message'], encoding='utf-8')
        print(f"  Downloaded and saved {len(df)} rows.")
        return df
    except Exception as e:
        print(f"  Download failed ({e}). Using built-in sample dataset…")
        return _builtin_dataset()


def _builtin_dataset() -> pd.DataFrame:
    """
    Built-in sample dataset (~400 messages) for offline training.
    Enough to produce a working model; accuracy will be lower than full dataset.
    """
    spam_messages = [
        "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121",
        "WINNER!! As a valued network customer you have been selected to receive a £900 prize reward!",
        "Urgent! Your mobile number has been awarded a £2000 Bonus Caller Prize on 10/06/03!",
        "Congratulations! You've been selected for a FREE iPhone. Click here to claim now!",
        "You have won a £1000 cash prize. To claim call 09058095201",
        "FREE MESSAGE: Congrats! You've been chosen for a free holiday to Tenerife!",
        "IMPORTANT - You could be entitled up to £3,160 in compensation from your company",
        "Urgent! Please call 09061749602. Airtime prize is awaiting collection.",
        "Win a £200 gift voucher! Take our 1 minute survey www.surveycentre.co.uk/mob",
        "Claim your £150 Amazon gift card NOW. Limited time. Visit: reward-gifts.tk",
        "You are a winner! Call us now at 07786200117 between 10am-7pm",
        "PRIVATE! Your 2003 Account Statement for 07742676969 shows 786 unredeemed Bonus Points",
        "Had your mobile 11mths? Update for FREE to the latest colour mobiles",
        "SIX chances to win CASH! From 100 to 20,000 pounds txt> CSH11",
        "Urgent! Your order has been selected for a security upgrade. Click: verify-now.ml",
        "FREE ringtone! Reply YES for your FREE ringtone and screensaver!",
        "Congrats! 1 year special cinema pass for 2 is yours. call 09061209465",
        "Your cash-balance is currently 500 pounds - to maximize your cash reward call 08714712412",
        "CLICK HERE for your FREE entry to our £250 prize draw: http://win.prizes.tk/draw",
        "Alert: Your bank account needs verification. Login: http://bank-verify.gq/login",
        "Congratulations ur awarded 500 of CD vouchers or 125gift guaranteed & Free entry 2",
        "IMPORTANT notice! You have won a free holiday. To claim text HOLIDAY to 80488",
        "FREE entry into our £500 prize draw. Text WIN to 86688 now!",
        "Your number has been randomly selected to receive a free laptop. Call 0800 123456",
        "You've been pre-selected to receive 3 months free broadband. Click to activate",
        "Naughty chat is just 25p/min. Call 0906 100 5350. Over 18? Girls are waiting!",
        "Text SEXY to 69911 for adult content. 18+. £1.50/msg",
        "Loan approved! Get £5000 today. No credit checks. Apply: http://loans.tk/apply",
        "DOUBLE your money with our guaranteed investment scheme. Contact info@bitcoin-profit.gq",
        "Nigerian Prince needs your help. I have $5,000,000 to transfer. Reply for details.",
        "Claim your FREE gift card worth $500 at Amazon. Limited offer. Click now!",
        "You have been charged £5 for a subscription. To cancel text STOP to 85233",
        "Get payday loan up to £1000. Instant approval. Bad credit OK. Apply now!",
        "Hot singles in your area are waiting. Text MEET to 69911",
        "Win iPod or £400 cash. Send your Name and address to Premium SMS",
    ] * 8  # replicate to get ~280 spam

    ham_messages = [
        "Hey, are you coming to the party tonight?",
        "Don't forget to pick up milk on your way home",
        "I'll be there in about 10 minutes, traffic is bad",
        "Can we reschedule our meeting to Thursday?",
        "Happy birthday! Hope you have an amazing day",
        "The project deadline has been moved to Friday",
        "What time does the movie start?",
        "I finished the report, I'll send it over shortly",
        "Thanks for lunch today, it was great catching up!",
        "Are you free this weekend? Let's hang out",
        "Just got home. Dinner is ready whenever you are",
        "Call me when you get a chance, need to talk",
        "The kids are doing great at school this term",
        "Did you see the game last night? Incredible ending!",
        "Running a bit late, will be there by 3pm",
        "Reminder: doctor's appointment tomorrow at 10am",
        "I sent you the files via email, let me know if received",
        "Weather is beautiful today, fancy a walk?",
        "Your package has been dispatched and will arrive tomorrow",
        "Meeting moved to conference room B at 2pm",
        "Can you bring the charger when you come?",
        "Hope your interview went well! Let me know how it went",
        "Dinner at 7? I'll book the restaurant",
        "The Wi-Fi password is on the fridge door",
        "See you at the gym tomorrow morning, usual time?",
        "Could you please review the attached document?",
        "The train is delayed by about 20 minutes",
        "Mum says dinner is at 6, don't be late",
        "I've attached the invoice to this message",
        "Let's sync up on the project later this afternoon",
        "Your prescription is ready to collect at the pharmacy",
        "Do you want tea or coffee? I'm making a round",
        "Just checking in, hope everything is okay",
        "I'll pick you up from the station at 5:30",
        "The plumber is coming between 2 and 4 tomorrow",
    ] * 10  # replicate to get ~350 ham

    labels   = ['spam'] * len(spam_messages) + ['ham'] * len(ham_messages)
    messages = spam_messages + ham_messages

    df = pd.DataFrame({'label': labels, 'message': messages})
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


# ════════════════════════════════════════════════════════════════════════════
# 2.  PREPROCESSING
# ════════════════════════════════════════════════════════════════════════════

def preprocess_text(text: str) -> str:
    """Clean and normalise a single SMS message."""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', ' url ', text)
    text = re.sub(r'\d+', ' num ', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    if STOPWORDS:
        words = text.split()
        words = [w for w in words if w not in STOPWORDS and len(w) > 1]
        text = ' '.join(words)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ════════════════════════════════════════════════════════════════════════════
# 3.  TRAINING
# ════════════════════════════════════════════════════════════════════════════

def train():
    print("\n" + "═" * 60)
    print("   CyberGuard — SMS Spam Model Training")
    print("═" * 60 + "\n")

    # ── Load ──────────────────────────────────────────────────────────────
    print("[1/5] Loading dataset…")
    df = load_dataset()
    df.dropna(subset=['label', 'message'], inplace=True)
    df['label'] = df['label'].str.strip().str.lower()

    print(f"  Total samples : {len(df)}")
    print(f"  Spam          : {(df['label'] == 'spam').sum()}")
    print(f"  Ham           : {(df['label'] == 'ham').sum()}")

    # ── Preprocess ────────────────────────────────────────────────────────
    print("\n[2/5] Preprocessing text…")
    df['clean'] = df['message'].apply(preprocess_text)

    # Binary encoding: spam=1, ham=0
    df['label_enc'] = (df['label'] == 'spam').astype(int)

    X = df['clean'].values
    y = df['label_enc'].values

    # ── Split ──────────────────────────────────────────────────────────────
    print("\n[3/5] Splitting data (80/20 train/test)…")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

    # ── Vectorise ──────────────────────────────────────────────────────────
    print("\n[4/5] Fitting TF-IDF Vectorizer…")
    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf  = vectorizer.transform(X_test)
    print(f"  Vocabulary size: {len(vectorizer.vocabulary_)}")

    # ── Train Models ───────────────────────────────────────────────────────
    print("\n[5/5] Training models…\n")

    # Primary: Multinomial Naive Bayes
    print("  → Multinomial Naive Bayes")
    nb_model = MultinomialNB(alpha=0.1)
    nb_model.fit(X_train_tfidf, y_train)
    nb_preds = nb_model.predict(X_test_tfidf)
    nb_acc   = accuracy_score(y_test, nb_preds)
    nb_auc   = roc_auc_score(y_test, nb_model.predict_proba(X_test_tfidf)[:, 1])

    print(f"     Accuracy : {nb_acc:.4f} ({nb_acc*100:.2f}%)")
    print(f"     ROC-AUC  : {nb_auc:.4f}")
    print("\n  Classification Report (Naive Bayes):")
    print(classification_report(y_test, nb_preds, target_names=['Ham', 'Spam']))

    # Optional: Logistic Regression
    print("  → Logistic Regression (comparison)")
    lr_model  = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    lr_model.fit(X_train_tfidf, y_train)
    lr_preds  = lr_model.predict(X_test_tfidf)
    lr_acc    = accuracy_score(y_test, lr_preds)
    print(f"     Accuracy : {lr_acc:.4f} ({lr_acc*100:.2f}%)\n")

    # ── Save ──────────────────────────────────────────────────────────────
    model_path      = MODELS_DIR / 'sms_model.pkl'
    vectorizer_path = MODELS_DIR / 'sms_vectorizer.pkl'
    lr_path         = MODELS_DIR / 'sms_model_lr.pkl'

    joblib.dump(nb_model,   str(model_path))
    joblib.dump(vectorizer, str(vectorizer_path))
    joblib.dump(lr_model,   str(lr_path))

    print("  ✓ Models saved:")
    print(f"    {model_path}")
    print(f"    {vectorizer_path}")
    print(f"    {lr_path}")

    # Save accuracy metadata
    meta_path = MODELS_DIR / 'sms_model_meta.txt'
    meta_path.write_text(
        f"Model: MultinomialNB\n"
        f"Accuracy: {nb_acc*100:.2f}%\n"
        f"ROC-AUC:  {nb_auc*100:.2f}%\n"
        f"Train size: {len(X_train)}\n"
        f"Test size:  {len(X_test)}\n"
        f"Vocabulary: {len(vectorizer.vocabulary_)}\n"
    )

    print("\n" + "═" * 60)
    print(f"  ✅ SMS Model Training Complete!")
    print(f"  Final Accuracy: {nb_acc*100:.2f}%  |  AUC: {nb_auc*100:.2f}%")
    print("═" * 60 + "\n")


if __name__ == '__main__':
    # Add project root to path for Django settings
    sys.path.insert(0, str(PROJECT_DIR))
    train()
