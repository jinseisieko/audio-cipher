
import numpy as np
description = "gauss + length is 60020 + noise*3"
def f(audio: np.ndarray, mean: float = 0.0, sigma: float = 0.06) -> np.ndarray:
    """Добавляем Гауссов шум."""
    noise = np.random.normal(mean, sigma, size=audio.shape).astype(np.float32)
    return np.clip(audio + noise, -1.0, 1.0)