# 🛡️ CyberGuard — SMS Spam & Malicious URL Detection System

## 📌 Overview

CyberGuard is a **full-stack machine learning web application** that detects:

* 📱 SMS messages as **Spam / Not Spam**
* 🌐 URLs as **Malicious / Safe**

The system uses **Natural Language Processing (NLP)** and **Machine Learning (ML)** models integrated into a **Django-based web application** with a responsive frontend.

This project demonstrates real-world cybersecurity techniques used in email filters, browsers, and fraud detection systems.

---

## 🚀 Features

* 🔍 SMS Spam Detection using ML
* 🔗 Malicious URL Detection using feature analysis
* 📊 Confidence Score & Risk Level display
* 🗂️ Prediction History with CSV export
* 🌐 REST API for integration
* 🎨 Responsive UI with Bootstrap

---

## 🧠 Machine Learning Models

| Module        | Algorithm               | Description                      |
| ------------- | ----------------------- | -------------------------------- |
| SMS Detection | Multinomial Naive Bayes | Text classification using TF-IDF |
| URL Detection | Random Forest           | Feature-based classification     |

---

## 📂 Dataset Used

### 📱 SMS Dataset

* UCI SMS Spam Collection Dataset (~5,574 messages)
* Labels: Spam / Ham

### 🌐 URL Dataset

* Combination of:

  * Built-in dataset (~1000 URLs)
  * Synthetic generated URLs
  * Optional custom dataset (`url_dataset.csv`)

---

## ⚙️ Tech Stack

* **Backend:** Python, Django, Django REST Framework
* **Machine Learning:** scikit-learn, pandas, numpy, nltk
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
* **Database:** SQLite
* **Tools:** VS Code, pip, virtualenv

---

## 🏗️ Project Structure

```
cyberguard/
│
├── spam_detector/        # SMS Spam Detection module
├── url_detector/         # URL Detection module
├── ml_training/          # Model training scripts
├── ml_models/            # Saved ML models (.pkl)
├── templates/            # HTML files
├── static/               # CSS & JS
├── manage.py
└── requirements.txt
```

---

## ⚡ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/cyberguard.git
cd cyberguard
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Train ML Models

```bash
python setup_models.py
```

### 5️⃣ Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ Run Server

```bash
python manage.py runserver
```

### 🌐 Open in Browser:

http://127.0.0.1:8000/

---

## 🔗 API Endpoints

| Endpoint          | Method | Description            |
| ----------------- | ------ | ---------------------- |
| /api/sms/predict/ | POST   | Predict SMS spam       |
| /api/url/predict/ | POST   | Detect malicious URL   |
| /api/history/     | GET    | Get prediction history |

---

## 📊 Model Performance

| Model             | Accuracy | AUC Score |
| ----------------- | -------- | --------- |
| SMS Spam Detector | ~97–98%  | ~99%      |
| URL Detector      | ~96–98%  | ~98%      |

---

## 🔄 How It Works

1. User enters SMS or URL
2. Data is preprocessed
3. Converted into numerical features
4. Passed to ML model
5. Prediction + confidence returned
6. Result displayed in UI and stored in database

---

## 🌍 Real-World Applications

* Email spam filters (Gmail, Outlook)
* Browser security (Chrome Safe Browsing)
* Banking fraud detection
* Telecom SMS filtering

---

## 👥 Team Roles

* 👨‍💻 Backend Developer (Django + API)
* 🤖 ML Engineer (Model training & prediction)
* 🗄️ Database Engineer (Logging & storage)
* 🎨 Frontend Developer (UI/UX)

---

## 📸 Screenshots

*Add screenshots of your project here*

---

## 📖 Future Improvements

* Deep Learning models (LSTM, BERT)
* Real-time threat detection
* Deployment on cloud (AWS, Azure)
* Mobile app integration

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## 📜 License

This project is for educational purposes.

---

## 🙌 Acknowledgements

* UCI Machine Learning Repository
* scikit-learn documentation
* Django community

---

## 💡 Author

**Your Name**
B.Tech CSE Student
Cybersecurity & AI Enthusiast

---
