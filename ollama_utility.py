"""
Ollama client utility — based on the pattern used by your instructor.
Uses the official `ollama` Python package (Client) instead of raw HTTP requests.
"""

from typing import Final, Optional
from ollama import Client, ChatResponse

import logging
import re


VERSION: Final[str] = "1.0"
TEMPERATURE: Final[float] = 0.1

MODEL_NAME: Final[str] = "llama3.1:8b"
BASE_URL_OFFLINE: Final[str] = "http://127.0.0.1:11434"

logger = logging.getLogger(name=__name__)
logger.addHandler(hdlr=logging.NullHandler())


def get_offline_client(base_url: str = BASE_URL_OFFLINE) -> Client:
    """Get a client pointing to a local Ollama server."""
    return Client(host=base_url)


def chat(
    messages: list[dict],
    think: bool = False,
    model_name: str = MODEL_NAME,
    temperature: float = TEMPERATURE,
    base_url: str = BASE_URL_OFFLINE,
) -> tuple[Optional[str], int, int]:
    """
    Chat with the local Ollama service.

    messages: list of {"role": "user"/"assistant"/"system", "content": "..."}
    Returns: (assistant_answer, prompt_tokens, completion_tokens)
    """

    client = get_offline_client(base_url=base_url)

    logger.debug(f"Ollama '{model_name}' chat started...")

    response: ChatResponse = client.chat(
        model=model_name,
        messages=messages,
        think=think,
        stream=False,
        options={
            "temperature": temperature,
            "num_ctx": 16384,
        },
    )

    logger.debug(f"Ollama '{model_name}' chat finished.")

    assistant_answer: Optional[str] = response.message.content

    prompt_tokens = response.prompt_eval_count or 0
    completion_tokens = response.eval_count or 0

    return assistant_answer, prompt_tokens, completion_tokens

def get_management_report(
    data_string: str,
    base_url: str = BASE_URL_OFFLINE,
    model_name: str = MODEL_NAME,
) -> str:
    """
    Generate a short Persian management report from a DataFrame output.
    """

    client = get_offline_client(base_url=base_url)

    system_prompt = """
You are a senior banking business analyst.

Write a concise management report in Persian.

The report must include:
- مهم‌ترین یافته
- تحلیل کوتاه
- پیشنهاد مدیریتی

Maximum 150 words.
"""

    response: ChatResponse = client.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Analyze the following table and write a management report in Persian:\n\n{data_string}",
            },
        ],
        options={
            "temperature": 0.2,
            "num_ctx": 4096,
        },
    )

    return response.message.content.strip()


GENERAL_PROMPT = """
You are an expert Python Pandas developer.

Your ONLY task is to convert a Persian user's question into executable Python Pandas code.

DataFrame name:

df

Columns:

{columns}

Sample data:

{sample_data_json}

Unique values:

{unique_values}

RULES

- Return ONLY executable Python code.
- No markdown.
- No explanations.
- No Persian text.
- Never invent column names.
- Use only existing columns.
- Always use astype(str).str.contains(..., case=False, na=False) for text searches.
- Handle missing values safely.

Return only executable Python code.
"""

COUNT_PROMPT = """
You are an expert Python Pandas developer.

Your ONLY task is to generate executable Python Pandas code.

DataFrame name:

df

Columns:

{columns}

Sample data:

{sample_data_json}

Unique values:

{unique_values}

The user is asking a COUNT question.

Examples:

چند
تعداد
چه تعداد
جمعا
چند نفر
چند تماس
چند مورد

RULES

- Return ONLY executable Python code.
- Never explain.
- Never return markdown.
- Never return Persian text.
- Never return lists.
- Never return phone numbers.
- Never return names.
- Never invent column names.
- Use only existing columns.
- Always use case=False and na=False in text searches.

Preferred functions:

len(...)
.nunique()
.value_counts()

Special Examples

Q: از استان مازندران چند تماس داشته ایم؟
A:
len(df[df["استان"].astype(str).str.contains("مازندران", case=False, na=False)])

Q: چند تماس از طرف بانک داشته ایم؟
A:
len(df[df["نوع متقاضی"].astype(str).str.contains("بانک", case=False, na=False)])

Q: از چند استان تماس داشته ایم؟
A:
df["استان"].dropna().nunique()

Q: جمعا چند متقاضی حقیقی و حقوقی تماس گرفته اند؟
A:
df["نوع متقاضی"].value_counts().to_dict()

Return ONLY executable Python code.
"""


LIST_PROMPT = """
You are an expert Python Pandas developer.

Your ONLY task is to generate executable Python Pandas code.

DataFrame name:

df

Columns:

{columns}

Sample data:

{sample_data_json}

Unique values:

{unique_values}

The user wants a LIST.

Examples

چه کسانی
چه اشخاصی
اسامی
لیست
کدام مشتریان

RULES

- Return ONLY executable Python code.
- Never explain.
- Never return markdown.
- Never summarize.
- Never return counts.
- Never invent column names.
- Use only existing columns.
- Always use case=False and na=False.

When the user asks:

چه کسانی

Return

.unique().tolist()

If user asks phone numbers

Return only phone number column.

If user asks actions

Return only action column.

Examples

Q: چه اشخاصی از استان فارس تماس گرفته اند؟

A:
df[df["استان"].astype(str).str.contains("فارس", case=False, na=False)]["نام متقاضی"].dropna().unique().tolist()

Q: شماره تماس آقای احمدی چیست؟

A:
df[df["نام متقاضی"].astype(str).str.contains("احمدی", case=False, na=False)]["شماره تماس"].dropna().tolist()

Q: اقدامات انجام شده برای آقای رضایی چیست؟

A:
df[df["نام متقاضی"].astype(str).str.contains("رضایی", case=False, na=False)]["اقدامات انجام شده"].dropna().tolist()

Return ONLY executable Python code.
"""



ANALYSIS_PROMPT = """
You are an expert Python Pandas analyst.

Your ONLY task is to generate executable Python Pandas code.

DataFrame name:

df

Columns:

{columns}

Sample data:

{sample_data_json}

Unique values:

{unique_values}

The user wants a MANAGEMENT ANALYSIS.

Examples

تحلیل
گزارش
بررسی
روند
وضعیت
خلاصه

RULES

- Return ONLY executable Python code.
- Never explain.
- Never return markdown.
- Never search for people's names.
- Never filter rows using fixed keywords.
- Never return phone numbers.
- Never return lists.
- Never invent column names.
- Use only existing columns.

Always produce a summarized DataFrame.

Preferred operations

groupby()

agg()

value_counts()

pivot_table()

reset_index()

sort_values()

Examples

Q: یک تحلیل کلی از جدول بده

A:
df.describe(include="all")

Q: تحلیل استان‌ها را بده

A:
df.groupby("استان").size().reset_index(name="تعداد").sort_values("تعداد", ascending=False)

Q: تحلیل نوع متقاضی

A:
df.groupby("نوع متقاضی").size().reset_index(name="تعداد")

Q: تحلیل اقدامات انجام شده

A:
df.groupby("اقدامات انجام شده").size().reset_index(name="تعداد").sort_values("تعداد", ascending=False)

The result MUST be a pandas DataFrame.

Return ONLY executable Python code.
"""

COUNT_KEYWORDS = [
    "چند",
    "تعداد",
    "چه تعداد",
    "جمعا",
    "جمع",
    "کل",
    "جمع کل",
    "آمار",
    "میزان",
    "چندتا",
    "چند مورد",
]

LIST_KEYWORDS = [
    "چه کسانی",
    "چه اشخاصی",
    "چه افرادی",
    "اسامی",
    "لیست",
    "افراد",
    "اشخاص",
    "مشتریان",
    "نام",
    "نام ها",
]

ANALYSIS_KEYWORDS = [
    "تحلیل",
    "گزارش",
    "روند",
    "بررسی",
    "وضعیت",
    "خلاصه",
]


def generate_pandas_code(
    question: str,
    columns: list[str],
    sample_data_json: str,
    unique_values: dict,
    base_url: str,
    model_name: str,
) -> str:
    """
    تبدیل سوال کاربر به کد پانداس با استفاده از ال‌ال‌ام
    """
    client = get_offline_client(base_url=base_url)
    
    # انتخاب Prompt مناسب

    if any(k in question for k in ANALYSIS_KEYWORDS):

        system_prompt = ANALYSIS_PROMPT.format(
            columns=columns,
            sample_data_json=sample_data_json,
            unique_values=unique_values,
        )

    elif any(k in question for k in COUNT_KEYWORDS):

        system_prompt = COUNT_PROMPT.format(
            columns=columns,
            sample_data_json=sample_data_json,
            unique_values=unique_values,
        )

    elif any(k in question for k in LIST_KEYWORDS):

        system_prompt = LIST_PROMPT.format(
            columns=columns,
            sample_data_json=sample_data_json,
            unique_values=unique_values,
        )

    else:

        system_prompt = GENERAL_PROMPT.format(
            columns=columns,
            sample_data_json=sample_data_json,
            unique_values=unique_values,
        )
    messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question},
]

    response = client.chat(
        model=model_name,
        messages=messages,
        options={
    "temperature": 0.0,
    "num_ctx": 8192,
    "stop": ["```"],
} # دما صفر برای دقت بالا در کدنویسی
    )
    
    # تمیز کردن خروجی جی‌پی‌تی از مارک‌داون احتمالی
    

    code = response.message.content.strip()

    # حذف markdown
    code = re.sub(r"```python", "", code)
    code = re.sub(r"```", "", code)

    # حذف importهای احتمالی
    code = code.replace("import pandas as pd", "")
    code = code.replace("import pandas", "")

    code = code.strip()

    return code

