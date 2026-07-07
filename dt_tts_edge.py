"""
Dariush Tasdighi Custom 'edge-tts' Package Module
"""

import time
import dt_utility as utility

from typing import Final
from edge_tts import Communicate

# __version__ = "2.3.0"
VERSION: Final[str] = "2.3.0"

RATE: Final[str] = "+5%"
PITCH: Final[str] = "-10Hz"
VOLUME: Final[str] = "+20%"

VOICES_MALE: Final[list[str]] = [
    "fa-IR-FaridNeural",
]

VOICES_FEMALE: Final[list[str]] = [
    "fa-IR-DilaraNeural",
]


def fix_text_for_speech(text: str) -> str:
    """
    Fix text for speech
    """

    fixed_text: str = f" {text} "

    fixed_text = fixed_text.replace(".", " . ")
    fixed_text = fixed_text.replace("؛", " . ")
    fixed_text = fixed_text.replace(",", " , ")
    fixed_text = fixed_text.replace("،", " ، ")
    fixed_text = fixed_text.replace("!", " ! ")
    fixed_text = fixed_text.replace("?", " ? ")
    fixed_text = fixed_text.replace("؟", " ؟ ")

    fixed_text = fixed_text.replace(" هسته‌ای ", " هَستِیی ")
    fixed_text = fixed_text.replace(" رای‌گیری ", " رَعْی گیری ")
    fixed_text = fixed_text.replace(" نخست‌وزیر ", " نُخُسْتْ وَزیر ")
    fixed_text = fixed_text.replace(" پرالتهاب ", " پُرْ اِلْتِهاب ")

    fixed_text = fixed_text.replace("‌", " ")

    fixed_text = fixed_text.replace(" دفن ", " دَفْنْ ")
    fixed_text = fixed_text.replace(" موعد ", " مُوعِد ")
    fixed_text = fixed_text.replace(" اهرم ", " اَهرُم ")
    fixed_text = fixed_text.replace(" مسکو ", " مُسکو ")
    fixed_text = fixed_text.replace(" نهفته ", " نَهُفْته ")
    fixed_text = fixed_text.replace(" گردان ", " گُرْدان ")
    fixed_text = fixed_text.replace(" بوشهر ", " بوشِحْر ")  # نکته
    fixed_text = fixed_text.replace(" سرتیپ ", " سَرتیپ ")
    fixed_text = fixed_text.replace(" پدافند ", " پَدافَند ")
    fixed_text = fixed_text.replace(" ناموجه ", " نامُوَجَح ")
    fixed_text = fixed_text.replace(" مکانیزم ", " مِکانیزْم ")

    fixed_text = fixed_text.replace(" هتک ", " هَتْکِ ")
    fixed_text = fixed_text.replace(" هتکِ ", " هَتْکِ ")

    fixed_text = fixed_text.replace(" اتم ", " اَتُم ")
    fixed_text = fixed_text.replace(" اتمی ", " اَتُمی ")

    fixed_text = fixed_text.replace(" افشا ", " اِفشا ")
    fixed_text = fixed_text.replace(" افشای ", " اِفْشایِ ")

    fixed_text = fixed_text.replace(" پهباد ", " پَهْباد ")
    fixed_text = fixed_text.replace(" پهبادها ", " پَهْبادْها ")
    fixed_text = fixed_text.replace(" پهبادهای ", " پَهْبادْهای ")

    fixed_text = fixed_text.replace(" سانتریفیو ", " سانتریفیوژ ")
    fixed_text = fixed_text.replace(" سانتریفیوها ", " سانتریفیوژها ")

    while "  " in fixed_text:
        fixed_text = fixed_text.replace("  ", " ")

    fixed_text = fixed_text.strip()

    return fixed_text


def convert_text_to_speech(
    text: str,
    audio_file_path: str,
    rate: str = RATE,
    pitch: str = PITCH,
    volume: str = VOLUME,
    voice: str = VOICES_FEMALE[0],
) -> tuple[int, float]:
    """
    Convert text to speech (Sync)
    """

    start_time: float = time.perf_counter()

    text = fix_text_for_speech(text=text)
    word_count: int = utility.get_word_count(text=text)

    communicate = Communicate(
        text=text,
        rate=rate,
        pitch=pitch,
        voice=voice,
        volume=volume,
    )

    communicate.save_sync(
        audio_fname=audio_file_path,
    )

    end_time: float = time.perf_counter()
    elapsed_time: float = end_time - start_time

    return word_count, elapsed_time


async def convert_text_to_speech_async(
    text: str,
    audio_file_path: str,
    rate: str = RATE,
    pitch: str = PITCH,
    volume: str = VOLUME,
    voice: str = VOICES_FEMALE[0],
) -> tuple[int, float]:
    """
    Convert text to speech (Async)
    """

    start_time: float = time.perf_counter()

    text = fix_text_for_speech(text=text)
    word_count: int = utility.get_word_count(text=text)

    communicate = Communicate(
        text=text,
        rate=rate,
        pitch=pitch,
        voice=voice,
        volume=volume,
    )

    await communicate.save(
        audio_fname=audio_file_path,
    )

    end_time: float = time.perf_counter()
    elapsed_time: float = end_time - start_time

    return word_count, elapsed_time


if __name__ == "__main__":
    utility.display_just_one_error_message(
        message=utility.ERROR_MESSAGE_MODULE_IS_NOT_EXECUTED_DIRECTLY,
    )
