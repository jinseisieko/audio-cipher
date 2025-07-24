
"""FastAPI сервис, кодирующий текст в WAV и декодирующий его обратно.

✦ Реализуйте функции `text_to_audio` и `audio_to_text`.
✦ Формат аудио: 44100Hz, 16‑bit PCM, mono.
"""

import base64
import io
import wave

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

SAMPLE_RATE = 44_100   # Hz
BIT_DEPTH = 16         # bits per sample
CHANNELS = 1

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": False})


# ---------------------------- pydantic models ---------------------------- #

class EncodeRequest(BaseModel):
    text: str = Field(..., description="Строка для кодирования в звук")


class EncodeResponse(BaseModel):
    data: str  # base64 wav


class DecodeRequest(BaseModel):
    data: str  # base64 wav


class DecodeResponse(BaseModel):
    text: str


# ---------------------------- helpers ---------------------------- #

def _empty_wav(duration_sec: float = 1.0) -> bytes:
    """Возвращает WAV‑байты тишины длиной *duration_sec*."""
    n_samples = int(SAMPLE_RATE * duration_sec)
    silence = np.zeros(n_samples, dtype=np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(silence.tobytes())
    return buf.getvalue()


# ---------------------------- TODO: your logic ---------------------------- #

def text_to_audio(text: str) -> bytes:
    """Зашифровать *text* в WAV.  
    Вернуть байтовое содержимое WAV‑файла."""
    # TODO: реализуйте алгоритм кодирования.
    #       Ниже временная заглушка: возвращаем 1сек тишины.
    return _empty_wav(1.0)


def audio_to_text(wav_bytes: bytes) -> str:
    """Декодировать WAV‑байты обратно в текст."""
    # TODO: реализуйте алгоритм декодирования.
    #       Ниже временная заглушка.
    return "<decoded text>"


# ---------------------------- endpoints ---------------------------- #

@app.post("/encode", response_model=EncodeResponse)
async def encode_text(request: EncodeRequest):
    wav_bytes = text_to_audio(request.text)
    wav_base64 = base64.b64encode(wav_bytes).decode("utf-8")
    return EncodeResponse(data=wav_base64)


@app.post("/decode", response_model=DecodeResponse)
async def decode_audio(request: DecodeRequest):
    wav_bytes = base64.b64decode(request.data)
    text = audio_to_text(wav_bytes)
    return DecodeResponse(text=text)


@app.get("/ping")
async def ping():
    return "ok"
