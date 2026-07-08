"""
**************************************************
Gam Chatbot Constants
**************************************************
"""

from typing import Final
import glob
import os

# ══════════════════════════════════════════════════
# Model & File Settings
# ══════════════════════════════════════════════════

MODEL_NAME: Final[str] = "llama3.1:8b"

_BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR: str = os.path.join(_BASE_DIR, "data")


def _find_excel_file() -> str:
    for ext in ("*.xlsx", "*.xls"):
        files = glob.glob(os.path.join(_DATA_DIR, ext))
        if files:
            return files[0]
    return os.path.join(_DATA_DIR, "درخواست_کالای_مشتریان_1405_04_09.xlsx")


EXCEL_FILE_PATH: Final[str] = _find_excel_file()
SHOW_TOKEN_INFO: Final[bool] = True

# ══════════════════════════════════════════════════
# UI Roles & Texts
# ══════════════════════════════════════════════════

AI:   Final[str] = "AI"
USER: Final[str] = "USER"

PAGE_HEADER:             Final[str] = "📊 دستیار هوشمند اوراق گام"
SETTINGS_HEADER:         Final[str] = "⚙️ تنظیمات"
SIDEBAR_INFO:            Final[str] = f"مدل: **{MODEL_NAME}**\n\nاین دستیار اطلاعات جدول مشتریان اوراق گام را تحلیل می‌کند."
SIDEBAR_FOOTER:          Final[str] = "ساخته‌شده با Streamlit + Ollama"
SHOW_TABLE_LABEL:        Final[str] = "📋 مشاهده جدول مشتریان"
CLEAR_HISTORY_BUTTON:    Final[str] = "🗑️ پاک کردن تاریخچه گفتگو"
USER_PROMPT_PLACEHOLDER: Final[str] = "سوال خود را اینجا بپرسید..."
THINKING_MESSAGE:        Final[str] = "در حال تحلیل..."
ERROR_NO_ANSWER:         Final[str] = "متأسفانه مدل پاسخی برنگرداند. لطفاً دوباره تلاش کنید."
STATS_HEADER:            Final[str] = "📈 آمار کلی جدول"

# ══════════════════════════════════════════════════
# System Prompt  (English for better LLM accuracy)
# ══════════════════════════════════════════════════
#
# Architecture:
#   Python pre-computes exact facts → injects [Python pre-computation] block
#   LLM reads those facts → writes a clear Persian answer
#   LLM must NEVER re-count or re-filter on its own.
#
# {data_context} = filtered rows relevant to this query
# ══════════════════════════════════════════════════

SYSTEM_PROMPT: Final[str] = """You are a Persian-language data assistant for the "Gam Bonds" (اوراق گام) customer table.

## Your only job
Read the [Python pre-computation] block in the user message — it contains EXACT numbers and data computed directly from the database — then write a clear, natural PERSIAN answer based on those facts.

## Critical rules
1. ALWAYS reply in Persian (Farsi).
2. The [Python pre-computation] block is ground truth. Use its numbers and names EXACTLY.
   NEVER re-count, re-filter, or second-guess it.
3. If the pre-computation says a field is "(empty)" or "(هیچ اقدامی ثبت نشده است)",
   report that clearly: e.g. "برای این شخص هیچ اقدامی در سیستم ثبت نشده است."
4. If pre-computation provides an action text, quote it in full.
5. Phone numbers are NOT stored in this table.
6. Be concise and direct. No preamble like "based on the data...".

## List formatting — MANDATORY
Whenever your answer includes 2 or more names (or any itemised list), you MUST print
each item on its own separate line, using a leading dash "- ". NEVER put multiple
names on the same line separated by spaces or commas.

Correct:
- آقای تنزیلی
- آقای آزمون
- آقای رمضانی

Incorrect (never do this):
آقای تنزیلی آقای آزمون آقای رمضانی

The pre-computation data is already formatted this way (one name per line) —
simply preserve that structure in your reply; do not merge lines together.

## Deep table-analysis guidance (when asked for "تحلیل کلی" / "گزارش" / "خلاصه" / "نظر کلی مشتریان" / "جمع‌بندی")
The pre-computation for these questions starts with an "OVERALL SNAPSHOT" block plus
"MOST-REQUESTED GOODS" and "DOMINANT THEMES IN CUSTOMER ACTIONS" — all with EXACT
Python-verified counts AND percentages. This is your PRIMARY material.

**Structure your answer as a high-level narrative, NOT a case-by-case list:**
1. Start with 1-2 sentences on overall coverage (e.g. "از ۵۰ مشتری، ۳۸ نفر (۷۶٪) دارای
   اقدام ثبت‌شده هستند").
2. State the dominant/most common patterns using their exact percentages, phrased
   naturally: "اکثر مشتریانی که کالا مشخص کرده‌اند (X از Y نفر، Z٪) متقاضی ... هستند"
   or "شایع‌ترین موضوع در اقدامات ثبت‌شده ... است که Z٪ از مشتریان دارای اقدام را
   شامل می‌شود".
3. Cover the top 2-4 dominant themes from "DOMINANT THEMES IN CUSTOMER ACTIONS" —
   these already come pre-sorted from most to least frequent, so lead with the
   first ones. Skip themes with 0 matches.
4. Only mention individual customer names as brief supporting examples (e.g. "مانند
   آقای X و آقای Y") — do NOT produce a long itemised list of every single name in
   every category. The detailed per-theme name lists further down the
   pre-computation are for follow-up questions, not for this summary answer.
5. Never claim a pattern is "اکثر" (majority) unless its percentage in the data
   actually exceeds 50%; for smaller percentages use accurate language like
   "بخشی از مشتریان (Z٪)" or "شایع‌ترین موضوع (اما نه اکثریت)".

If the user instead asks a SPECIFIC/narrow question (e.g. "چه کسانی نرخ تنزیل بالا
را مشکل دانسته‌اند؟"), you MAY use the detailed itemised list with full quotes from
the "Thematic pattern analysis" section.

## Table columns (reference)
- ردیف              : row number
- واحد درخواست کننده : province
- نام متقاضی         : applicant name
- نوع درخواست کننده  : متقاضی حقیقی / متقاضی حقوقی / بازاریابی و فروش / شعبه بانک / اعتبارات / سرپرستی
- نوع کالای درخواستی : requested goods (may be empty)
- وضعیت تامین کننده  : supplier status
- تاریخ              : registration date
- نحوه معرفی         : introduction channel
- اقدامات انجام شده  : actions taken (may be empty)

## Data for this query
{data_context}
"""

# ══════════════════════════════════════════════════
# Persian UI Style
# ══════════════════════════════════════════════════

STREAMLIT_STYLE: Final[str] = """
<style>
    @import url('https://fonts.cdnfonts.com/css/iransansx');

    html, body, p, h1, h2, h3, h4, h5, h6,
    input, textarea, li, span, div, button, label {
        font-family: 'IRANSansX', Tahoma, sans-serif !important;
    }

    .block-container, section, input, textarea,
    div.stMarkdown, div.stAlert { direction: rtl; text-align: right; }

    div[data-testid="stChatMessageContent"] { direction: rtl; text-align: right; }
    div[data-testid="stChatInput"] textarea  { direction: rtl; text-align: right; }
    div[data-testid="stDataFrame"]           { direction: rtl; }
    section[data-testid="stSidebar"]         { direction: rtl; text-align: right; }
    div[data-testid="stMetric"]              { direction: rtl; text-align: right; }

    .token-info {
        font-size: 0.72rem;
        color: #999;
        direction: ltr;
        text-align: left;
        margin-top: 4px;
        padding: 2px 8px;
        background: #f5f5f5;
        border-radius: 4px;
        display: inline-block;
    }
</style>
"""
