
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
ONE_SIZE = 32768

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
    n_samples = int(SAMPLE_RATE * 10)
    line = np.zeros(n_samples, dtype=np.int16) 

    # for i, char in enumerate(text):
    #     line[i] = int(char)+1
    i = 0
    for char in text:
        t = int(char)
        t = ONE_SIZE/12*(t+1)
        line[i] = t
        i += 1
        line[i] = t
        i += 1
        line[i] = t
        i += 1
    

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(line.tobytes())
    return buf.getvalue()


def audio_to_text(wav_bytes: bytes) -> str:
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == CHANNELS
        assert wf.getsampwidth() == BIT_DEPTH // 8
        assert wf.getframerate() == SAMPLE_RATE

        frames = wf.readframes(wf.getnframes())
    
    line = np.frombuffer(frames, dtype=np.int16)
    i = 0
    res = ''
    while line[i] > ONE_SIZE/12-ONE_SIZE/24:
        can = []
        t = line[i]-1
        for j in range(10):
            if ONE_SIZE/12*(j+1)-ONE_SIZE/24 <= t <= ONE_SIZE/12*(j+1)+ONE_SIZE/24:
                can.append(str(j))
                break
        i += 1
        t = line[i]-1
        for j in range(10):
            if ONE_SIZE/12*(j+1)-ONE_SIZE/24 <= t <= ONE_SIZE/12*(j+1)+ONE_SIZE/24:
                can.append(str(j))
                break
        i += 1
        t = line[i]-1
        for j in range(10):
            if ONE_SIZE/12*(j+1)-ONE_SIZE/24 <= t <= ONE_SIZE/12*(j+1)+ONE_SIZE/24:
                can.append(str(j))
                break
        i += 1
        for e in can:
            if can.count(e) > 1:
                res += e
                break
        else:
            res += can[0]
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
