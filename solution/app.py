
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
MIN_VAL = -32768
MAX_VAL = 32767
NUM_BINS = 11
CELL_SIZE = 5

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

def digit_to_average_sample(digit: int) -> int:
    step = (MAX_VAL - MIN_VAL + 1) / NUM_BINS
    range_start = MIN_VAL + int(digit * step)
    range_end = MIN_VAL + int((digit + 1) * step) - 1
    average = (range_start + range_end) // 2
    return average

def sample_to_digit(sample: int) -> int:
    step = (MAX_VAL - MIN_VAL + 1) / NUM_BINS
    shifted = sample - MIN_VAL
    bin_index = int(shifted // step)
    return min(bin_index, NUM_BINS - 1)


def text_to_audio(text: str) -> bytes:
    n_samples = int(SAMPLE_RATE * 10)
    line = np.zeros(n_samples, dtype=np.int16) 

    i = 0
    while i < n_samples:
        for char in text:
            t = int(char)
            for _ in range(CELL_SIZE):
                line[i] = digit_to_average_sample(t)
                i += 1
                if i >= n_samples:
                    break
            if i >= n_samples:
                break
        if i >= n_samples:
            break
        for _ in range(CELL_SIZE):
            line[i] = digit_to_average_sample(10)
            i += 1
            if i >= n_samples:
                break

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(line.tobytes())
    return buf.getvalue()


def audio_to_text(wav_bytes: bytes) -> str:
    n_samples = int(SAMPLE_RATE * 10)
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == CHANNELS
        assert wf.getsampwidth() == BIT_DEPTH // 8
        assert wf.getframerate() == SAMPLE_RATE

        frames = wf.readframes(wf.getnframes())
    
    line = np.frombuffer(frames, dtype=np.int16)
    res = ''
    can = [[]]
    i = 0
    j = 0
    while i < n_samples:
        h = []
        for _ in range(CELL_SIZE):
            h.append(line[i])
            i += 1
            if i >= n_samples:
                break
        sum_ = 0
        for e in h:
            sum_ += int(e)
        av = sum_/len(h)
        t = sample_to_digit(av)
        if t == 10:
            j = 0
        else:
            if j >= len(can):
                can.append([])
            can[j].append(t)
            j += 1

    for can_x in can[:-1]:
        for x in can_x:
            if can_x.count(x) > len(can_x)/2:
                res += str(x)
                break
        else:
            res += str(can_x[0])
    return res


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
