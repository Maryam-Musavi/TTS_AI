"""
Streamlit Excel Q&A Chatbot - Final Version (Text-to-Python Engine)
"""

import json
import re
import streamlit as st
import pandas as pd

import ollama_utility

# =========================
# Config
# =========================
MODEL_NAME = "llama3.1:8b"
BASE_URL = "http://127.0.0.1:11434"
TEMPERATURE = 0.1

POSSIBLE_PROVINCE_COLUMNS = [
    "استان", "شهر", "محل", "آدرس", "موقعیت", "منطقه",
    "واحد درخواست کننده", "نام متقاضی",
]

# =========================
# Province keywords for smart routing
# =========================
PROVINCE_KEYWORDS = [
    "آذربایجان", "اردبیل", "البرز", "بوشهر", "تهران",
    "خراسان", "خوزستان", "سمنان", "فارس", "قم",
    "کردستان", "کرمان", "کهگیلویه", "گیلان", "مازندران",
    "همدان", "یزد", "اصفهان", "زنجان", "سیستان",
]

COUNT_KEYWORDS = ["چند", "تعداد", "چه تعداد", "چه میزان", "count", "how many"]
DETAIL_KEYWORDS = ["چه کسانی", "چه اشخاصی", "اسامی", "نام", "اقدام", "تاریخ", "کی", "چه زمانی"]


def is_count_question(text: str) -> bool:
    return any(kw in text for kw in COUNT_KEYWORDS)


def is_detail_question(text: str) -> bool:
    return any(kw in text for kw in DETAIL_KEYWORDS)


def get_province_from_question(text: str, provinces_count: dict) -> str | None:
    """Extract province name from user question."""
    for province in provinces_count.keys():
        if province in text:
            return province
    for kw in PROVINCE_KEYWORDS:
        if kw in text:
            for province in provinces_count.keys():
                if kw in province:
                    return province
    return None


def answer_count_directly(question: str, data_summary: dict) -> str | None:
    """Answer count questions directly from pre-calculated data."""
    if not is_count_question(question):
        return None

    province = get_province_from_question(question, data_summary["provinces_count"])
    if province:
        count = data_summary["provinces_count"].get(province, 0)
        return f"از استان {province}، **{count} تماس گیرنده** داریم."

    # کلمه کلیدی عمومی "استان" از اینجا حذف شد تا سوالات تحلیلی استان‌ها به بخش هوش مصنوعی هدایت شوند
    general_stats = {
        "دارندگان اوراق": "تعداد دارندگان اوراق گام",
        "متقاضی": "تعداد دارندگان اوراق گام",
        "همکاران استانی": "تعداد تماس همکاران استانی بانک",
        "استان فعال": "تعداد استان های فعال",
    }

    stats_map = data_summary.get("stats_map", {})
    for keyword, stats_key in general_stats.items():
        if keyword in question and stats_key in stats_map:
            return f"**{stats_key}**: {stats_map[stats_key]}"

    return None


def answer_actions_directly(question: str, df: pd.DataFrame) -> str | None:
    """Answer questions about actions for a specific person directly from pandas."""
    action_triggers = ["اقدام", "چه کاری", "چه کارهایی", "انجام شده", "پیگیری"]
    if not any(kw in question for kw in action_triggers):
        return None

    # Find name column
    name_col = None
    for col in ["نام متقاضی", "نام", "متقاضی", "نام تماس گیرنده"]:
        if col in df.columns:
            name_col = col
            break
    if not name_col:
        return None

    # Find actions column
    action_col = None
    for col in ["اقدامات انجام شده", "اقدام", "اقدامات", "پیگیری", "توضیحات"]:
        if col in df.columns:
            action_col = col
            break
    if not action_col:
        return None

    all_names = sorted(
        df[name_col].dropna().unique(),
        key=lambda x: len(str(x)),
        reverse=True
    )
    matched_name = None
    best_match_len = 0

    for name in all_names:
        name_str = str(name).strip()
        clean_name = name_str.replace("آقای", "").replace("خانم", "").strip()
        if clean_name and clean_name in question:
            if len(clean_name) > best_match_len:
                matched_name = name_str
                best_match_len = len(clean_name)

    if not matched_name:
        for name in all_names:
            name_str = str(name).strip()
            parts = name_str.replace("آقای", "").replace("خانم", "").strip().split()
            for part in sorted(parts, key=len, reverse=True):
                if len(part) > 3 and part in question:
                    if len(part) > best_match_len:
                        matched_name = name_str
                        best_match_len = len(part)
                    break

    if not matched_name:
        return None

    search_term = matched_name.replace("آقای", "").replace("خانم", "").strip()
    mask = df[name_col].astype(str).str.contains(search_term, na=False)
    filtered = df[mask]

    if filtered.empty:
        return f"هیچ رکوردی برای **{matched_name}** پیدا نشد."

    date_col = next((c for c in ["تاریخ", "تاریخ تماس", "date"] if c in df.columns), None)

    lines = [f"اقدامات انجام شده برای **{matched_name}**:"]
    for i, (_, row) in enumerate(filtered.iterrows(), 1):
        action = str(row[action_col]).strip()
        date_str = ""
        if date_col:
            date_val = str(row[date_col]).strip()
            if date_val and date_val != "nan":
                date_str = f" (تاریخ: {date_val})"
        if action and action != "nan":
            lines.append(f"{i}. {action}{date_str}")
        else:
            lines.append(f"{i}. اقدامی ثبت نشده{date_str}")

    return "\n".join(lines)


def answer_names_directly(question: str, data_summary: dict, df: pd.DataFrame) -> str | None:
    """Answer 'who contacted from X province' directly from pandas."""
    name_triggers = ["چه اشخاصی", "چه کسانی", "اسامی", "چه نام", "چه افرادی", "لیست افراد"]
    if not any(kw in question for kw in name_triggers):
        return None

    province = get_province_from_question(question, data_summary["provinces_count"])
    if not province:
        return None

    province_col = data_summary.get("province_column")
    if not province_col or province_col not in df.columns:
        for col in df.columns:
            if df[col].astype(str).str.contains(province, na=False).any():
                province_col = col
                break

    if not province_col:
        return None

    mask = df[province_col].astype(str).str.contains(province, na=False)
    filtered = df[mask]

    if filtered.empty:
        return f"هیچ رکوردی برای استان {province} در داده‌ها پیدا نشد."

    name_col = None
    for col in ["نام متقاضی", "نام", "متقاضی", "نام تماس گیرنده", "اسم"]:
        if col in df.columns:
            name_col = col
            break

    if not name_col:
        for col in df.columns:
            if df[col].dtype == object and col != province_col:
                name_col = col
                break

    if not name_col:
        return None

    names = filtered[name_col].dropna().unique().tolist()
    names = [str(n).strip() for n in names if str(n).strip() and str(n).strip() != "nan"]

    if not names:
        return f"نامی برای استان {province} در ستون '{name_col}' یافت نشد."

    names_list = "\n".join(f"- {n}" for n in names)
    return f"اشخاص تماس گیرنده از استان **{province}** ({len(names)} نفر):\n{names_list}"


# =========================
# Data loading
# =========================
@st.cache_data(show_spinner=False)
def load_and_analyze_data(file_bytes: bytes):

    all_sheets = pd.read_excel(
        pd.io.common.BytesIO(file_bytes),
        sheet_name=None,
        engine="openpyxl"
    )

    sheet_names = list(all_sheets.keys())

    df = all_sheets[sheet_names[0]]

    unique_values = {}

    for col in [
        "استان",
        "نوع متقاضی",
        "اقدامات انجام شده",
        "نام متقاضی",
    ]:
        if col in df.columns:
            unique_values[col] = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
    all_sheets = pd.read_excel(
        pd.io.common.BytesIO(file_bytes),
        sheet_name=None,
        engine="openpyxl"
    )

    sheet_names = list(all_sheets.keys())
    df = all_sheets[sheet_names[0]]

    stats_text = ""
    provinces_count = {}
    stats_map = {}

    if len(all_sheets) >= 2:
        stats_df = all_sheets[sheet_names[1]]

        header_lines = ["== خلاصه کلی =="]
        for _, row in stats_df.iterrows():
            cells = [str(v).strip() for v in row if pd.notna(v) and str(v).strip() not in ("", "nan")]
            if len(cells) == 2:
                try:
                    val = float(cells[1])
                    header_lines.append(f"{cells[0]}: {int(val)}")
                    stats_map[cells[0]] = int(val)
                except Exception:
                    pass

        province_data = {}
        for _, row in stats_df.iterrows():
            row_vals = [v for v in row if pd.notna(v) and str(v).strip() not in ("", "nan")]
            for i in range(len(row_vals) - 1):
                val = str(row_vals[i]).strip()
                next_val = str(row_vals[i + 1]).strip()
                skip_words = ["Row Labels", "Sum", "Grand", "Total", "تعداد", "1", "2", "3",
                              "4", "5", "6", "7", "8", "9", "10", "11", "12", "13",
                              "14", "15", "16", "17", "18", "19", "20"]
                try:
                    count = float(next_val)
                    if not any(s in val for s in skip_words) and len(val) > 2:
                        base_name = val.split("(")[0].strip()
                        province_data[base_name] = province_data.get(base_name, 0) + int(count)
                except Exception:
                    pass

        provinces_count = province_data

        province_lines = ["\n== تعداد تماس گیرنده از هر استان =="]
        for prov, count in sorted(provinces_count.items(), key=lambda x: x[1], reverse=True):
            province_lines.append(f"{prov}: {count} تماس")

        stats_text = "\n".join(header_lines + province_lines)

    province_col = None
    for col in POSSIBLE_PROVINCE_COLUMNS:
        if col in df.columns:
            province_col = col
            break

    if not provinces_count:
        if province_col:
            for value in df[province_col].dropna():
                val_str = str(value).strip()
                if val_str and val_str != "nan":
                    provinces_count[val_str] = provinces_count.get(val_str, 0) + 1

    summary = {
        "total_records": len(df),
        "unique_provinces": len(provinces_count),
        "provinces_count": provinces_count,
        "province_column": province_col,
        "all_columns": df.columns.tolist(),
        "stats_text": stats_text,
        "stats_map": stats_map,
        "unique_values": unique_values,
    }
    return summary, df


# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="چت بات اکسل با Ollama", page_icon="🤖", layout="wide")
st.title("🤖 چت بات هوشمند برای سوالات از داده‌های اکسل")
st.caption(f"مدل: `{MODEL_NAME}` — از طریق سرور محلی Ollama")

with st.sidebar:
    st.header("⚙️ تنظیمات")
    uploaded_file = st.file_uploader("فایل اکسل را بارگذاری کنید", type=["xlsx"])
    model_name = st.text_input("نام مدل", value=MODEL_NAME)
    base_url = st.text_input("آدرس سرور Ollama", value=BASE_URL)
    temperature = st.slider("Temperature", 0.0, 1.0, TEMPERATURE, 0.05)

    if st.button("🗑️ پاک کردن مکالمه"):
        st.session_state.pop("messages", None)
        st.rerun()

if uploaded_file is None:
    st.info("⬅️ لطفاً ابتدا یک فایل اکسل (.xlsx) از نوار کناری بارگذاری کنید.")
    st.stop()

data_summary, df = load_and_analyze_data(uploaded_file.getvalue())

# Stats panel
with st.expander("📊 آمار سریع داده‌ها", expanded=True):
    col1, col2 = st.columns(2)
    col1.metric("تعداد کل رکوردها", data_summary["total_records"])
    col2.metric("تعداد استان/شهر یکتا", data_summary["unique_provinces"])

    sorted_provinces = sorted(
        data_summary["provinces_count"].items(), key=lambda x: x[1], reverse=True
    )
    if sorted_provinces:
        stats_df_display = pd.DataFrame(sorted_provinces, columns=["استان/شهر", "تعداد تماس"])
        st.dataframe(stats_df_display, use_container_width=True)

    st.dataframe(df.head(10), use_container_width=True)

# Chat state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("سوال خود را درباره داده‌ها بپرسید...")

# 🌟🌟🌟 بخش جایگزین شده اصلی از اینجا شروع می‌شود 🌟🌟🌟
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # ۱. ابتدا بررسی فیلترهای مستقیم پایتونی شما (سریع و بدون مدل)
        direct_answer = answer_count_directly(user_input, data_summary)
        if not direct_answer:
            direct_answer = answer_actions_directly(user_input, df)
        if not direct_answer:
            direct_answer = answer_names_directly(user_input, data_summary, df)

        if direct_answer:
            st.markdown(direct_answer)
            st.caption("🔢 پاسخ مستقیم از فرمول‌های پیش‌فرض پانداس")
            st.session_state.messages.append({"role": "assistant", "content": direct_answer})
        
        else:
           # ۲. رویکرد Text-to-Python برای سوالات تحلیلی مدیریتی شما
            with st.spinner("در حال تحلیل هوشمند داده‌های اکسل..."):
                try:
                    # ایجاد یک نمونه کوچک از داده‌ها برای فهم ساختار توسط مدل
                    sample_data = df.head(3).to_json(orient="records", force_ascii=False)
                    
                    # تولید کد پانداس توسط Ollama
                    generated_code = ollama_utility.generate_pandas_code(
                        question=user_input,
                        columns=data_summary["all_columns"],
                        sample_data_json=sample_data,
                        unique_values=unique_values,
                        base_url=base_url,
                        model_name=model_name,
                    )
                    
                    # دیباگ داخلی برای ادمین جهت مشاهده کد پانداس ساخته شده
                    st.caption(f"💻 کد پانداس اجرا شده: `{generated_code}`")
                    
                    # 🌟 اصلاح مهم ۱: اضافه کردن str به دیکشنری محلی برای حل خطای اجرای کد
                    local_vars = {'df': df, 'pd': pd, 'str': str, 'int': int, 'float': float}

                    if not generated_code or not str(generated_code).strip():
                        raise ValueError("کد تولید شده خالی است.")

                    result = eval(generated_code, {"__builtins__": {}}, local_vars)

                    # 🌟 اصلاح مهم ۲: زیباسازی و فرمت‌دهی به انواع خروجی‌های پانداس برای نمایش به مدیر
                    if isinstance(result, list):
                        if result:
                            formatted_answer = "📋 **لیست افراد/موارد یافت شده:**\n" + "\n".join(f"- {item}" for item in result)
                        else:
                            formatted_answer = "🔍 هیچ موردی یافت نشد."
                            
                    elif isinstance(result, dict):
                        formatted_answer = "📊 **آمار تفکیکی:**\n" + "\n".join(f"- {k}: {v}" for k, v in result.items())
                        
                    elif isinstance(result, pd.Series):
                        # تبدیل خروجی‌های value_counts به یک جدول شکیل و مرتب
                        series_df = result.reset_index()
                        series_df.columns = ["عنوان / دسته‌بندی", "تعداد"]
                        st.dataframe(series_df, use_container_width=True)
                        formatted_answer = "📊 آمار درخواستی در جدول بالا استخراج و مرتب شد."
                        
                    elif isinstance(result, pd.DataFrame):
                        if not result.empty:
                            st.dataframe(result, use_container_width=True)
                            with st.spinner("در حال نگارش گزارش مدیریتی بر اساس نتایج..."):
                                report = ollama_utility.get_management_report(
                                    data_string=result.head(20).to_string(),
                                    base_url=base_url,
                                    model_name=model_name
                                )
                            formatted_answer = (
                                f"💡 تعداد {len(result)} ردیف استخراج شد.\n\n"
                                f"**گزارش مدیریتی:**\n{report}"
                            )
                        else:
                            formatted_answer = "🔍 رکوردی با این مشخصات یافت نشد."

                    else:
                        formatted_answer = f"✅ نتیجه: {result}"


                    
                except Exception as e:
                    formatted_answer = f"❌ متاسفانه در استخراج دقیق این گزارش خطایی رخ داد. لطفاً سوال را واضح‌تر بپرسید. \n*(جزئیات فنی: {e})*"

            st.markdown(formatted_answer)
            st.session_state.messages.append({"role": "assistant", "content": formatted_answer})