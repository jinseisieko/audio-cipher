import numpy as np
from typing import Union

description = "impulse noise + length 22785 + normal distribution + noise*5 (5%)"

def f(audio: np.ndarray, 
      noise_prob: float = 0.05, 
      noise_amplitude: Union[float, tuple] = 0.5) -> np.ndarray:
    mask = np.random.random(size=audio.shape) < noise_prob
    if isinstance(noise_amplitude, tuple):
        neg_amp, pos_amp = noise_amplitude
        noise = np.where(
            np.random.random(size=audio.shape) < 0.5,
            -neg_amp,
            pos_amp
        )
    else:
        noise = np.where(
            np.random.random(size=audio.shape) < 0.5,
            -noise_amplitude,
            noise_amplitude
        )
    noisy_audio = audio + mask * noise
    return np.clip(noisy_audio, -1.0, 1.0)