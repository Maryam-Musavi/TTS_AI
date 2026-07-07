# 📊 دستیار هوشمند اوراق گام

پروژه گزارش‌گیری هوشمند از جدول مشتریان اوراق گام با استفاده از **Llama 3.1:8b** و **Streamlit**

---

## 📁 ساختار پروژه

```
TTS-AI/
│
├── streamlit_app.py # فایل اصلی Streamlit (UI)
├── gam_constants.py # ثابت‌ها و تنظیمات
├── gam_functions.py # توابع کمکی (بارگذاری داده، ساخت prompt)
├── dt_ollama.py # ماژول ارتباط با Ollama
├── dt_tts_edge.py # ماژول تبدیل متن به گفتار (Text-to-Speech)
├── dt_utility.py # توابع کمکی عمومی
├── requirements.txt # پکیج‌های مورد نیاز
├── README.md # این فایل
│
├── data/
│ └── درخواست_کالای_مشتریان_1405_04_09.xlsx # فایل اکسل مشتریان
│
└── temp/ # پوشه موقت برای فایل‌های صوتی (به‌صورت خودکار ساخته می‌شود)
```

---

## ⚙️ پیش‌نیازها

### ۱. نصب Ollama
از سایت [ollama.com](https://ollama.com) دانلود و نصب کنید.

### ۲. دانلود مدل Llama 3.1:8b
```bash
ollama pull llama3.1:8b
```

### ۳. نصب پکیج‌های Python
```bash
pip install -r requirements.txt
```

---

# ساخت محیط مجازی با نام .venv
python -m venv .venv

# یا با نسخه خاص پایتون
py -3.13 -m venv .venv

## 🚀 اجرای پروژه

```bash
streamlit run ./streamlit_app.py
```

---

.\.venv\Scripts\Activate.ps1


.\.venv\Scripts\activate.bat


source .venv/bin/activate

---

# نمایش لیست پکیج‌های نصب شده
pip list

# بررسی نصب edge-tts
python -c "from edge_tts import Communicate; print('✅ edge-tts installed successfully!')"

# بررسی نصب streamlit
streamlit --version

---

## 📂 مراحل راه‌اندازی

1. پوشه `data/` را بسازید
2. فایل اکسل مشتریان را داخل پوشه `data/` کپی کنید
3. Ollama را اجرا کنید: `ollama serve`
4. پروژه را اجرا کنید: `streamlit run ./streamlit_app.py`

---

## 💬 نمونه سوالات

| سوال | توضیح |
|------|-------|
| کلاً از چند استان تماس گیرنده داشتیم؟ | آمار کلی استان‌ها |
| چند متقاضی حقیقی و حقوقی داریم؟ | تفکیک نوع متقاضیان |
| چه اشخاصی از استان مازندران تماس گرفته‌اند؟ | فیلتر بر اساس استان |
| اقدامات انجام شده برای آقای روحی مقدم؟ | جزئیات یک شخص خاص |
| چه کالاهایی درخواست شده است؟ | آمار انواع کالا |
| چند نفر تامین کننده دارند؟ | آمار وضعیت تامین کننده |

---

## 🏗️ معماری

```
کاربر → Streamlit UI → gam_functions.py → dt_ollama.py → Ollama (llama3.1:8b)
                              ↑
                    داده‌های اکسل (system prompt)
                              ↓
                    dt_tts_edge.py → پخش صوتی پاسخ
```

### نحوه کار:
- داده‌های کامل اکسل در **system prompt** به مدل ارسال می‌شود
- مدل با دسترسی کامل به جدول، سوالات را پاسخ می‌دهد
- تاریخچه گفتگو در **session_state** نگهداری می‌شود

---

## ⚙️ تنظیمات (در `gam_constants.py`)

| متغیر | مقدار پیش‌فرض | توضیح |
|-------|--------------|-------|
| `MODEL_NAME` | `llama3.1:8b` | نام مدل Ollama |
| `EXCEL_FILE_PATH` | `./data/...xlsx` | مسیر فایل اکسل |
| `SHOW_TOKEN_INFO` | `False` | نمایش تعداد توکن |

---

## 📝 نکات مهم

- **شماره تماس:** در جدول موجود نیست؛ مدل این را به کاربر توضیح می‌دهد
- **دما (Temperature):** روی `0.3` تنظیم شده برای دقت بیشتر در تحلیل داده
- **کش داده:** DataFrame یک‌بار بارگذاری و در session_state ذخیره می‌شود
