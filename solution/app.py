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
CELL_SIZE = 6
TERMINATOR_COUNT = 2

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
    n_samples = int(SAMPLE_RATE * duration_sec)
    silence = np.zeros(n_samples, dtype=np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(silence.tobytes())
    return buf.getvalue()


# ---------------------------- TODO: logic ---------------------------- #

def digit_to_sample_value(digit: int) -> int:
    step = (MAX_VAL - MIN_VAL + 1) / NUM_BINS
    range_start = MIN_VAL + int(digit * step)
    range_end = MIN_VAL + int((digit + 1) * step) - 1
    average = (range_start + range_end) // 2
    return average

def sample_to_digit_value(sample: int) -> int:
    step = (MAX_VAL - MIN_VAL + 1) / NUM_BINS
    shifted = sample - MIN_VAL
    bin_index = int(shifted // step)
    return min(bin_index, NUM_BINS - 1)


def text_to_audio(text: str) -> bytes:
    total_samples = int(SAMPLE_RATE * 10)
    audio_data = np.zeros(total_samples, dtype=np.int16) 

    sample_index = 0
    while sample_index < total_samples:
        for char in text:
            digit = int(char)
            for _ in range(CELL_SIZE):
                audio_data[sample_index] = digit_to_sample_value(digit)
                sample_index += 1
                if sample_index >= total_samples:
                    break
            if sample_index >= total_samples:
                break
        if sample_index >= total_samples:
            break
        for _ in range(TERMINATOR_COUNT):
            for _ in range(CELL_SIZE):
                audio_data[sample_index] = digit_to_sample_value(10)
                sample_index += 1
                if sample_index >= total_samples:
                    break
            if sample_index >= total_samples:
                break

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


def audio_to_text(wav_bytes: bytes) -> str:
    total_samples = int(SAMPLE_RATE * 10)
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == CHANNELS
        assert wf.getsampwidth() == BIT_DEPTH // 8
        assert wf.getframerate() == SAMPLE_RATE

        frames = wf.readframes(wf.getnframes())
    
    audio_samples = np.frombuffer(frames, dtype=np.int16)
    result_text = ''
    digit_groups = [[]]
    group_index = 0
    
    sample_index = 0
    while sample_index < total_samples:
        cell_samples = []
        for _ in range(CELL_SIZE):
            cell_samples.append(int(audio_samples[sample_index]))
            sample_index += 1
            if sample_index >= total_samples:
                break
        
        sample_sum = sum(cell_samples)
        avg_sample = sample_sum / len(cell_samples)
        digit = sample_to_digit_value(int(avg_sample))
        
        if digit == 10:
            group_index = 0
        else:
            if group_index >= len(digit_groups):
                digit_groups.append([])
            digit_groups[group_index].append(digit)
            group_index += 1

    for group in digit_groups[:-1]:
        found_majority = False
        for digit in group:
            if group.count(digit) > len(group) / 2:
                result_text += str(digit)
                found_majority = True
                break
        if not found_majority and group:
            result_text += str(group[0])
            
    return result_text


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