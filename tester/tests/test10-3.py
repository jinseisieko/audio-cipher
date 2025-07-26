import numpy as np
description = "pink + length is 5671 + noise*2"
def f(audio: np.ndarray, snr_db: float = 10.0) -> np.ndarray:
    """Add PINK noise with given SNR."""
    power_signal = np.mean(audio ** 2)
    power_noise = power_signal / (10 ** (snr_db / 10))
    
    # Генерируем розовый шум вместо белого
    pink_noise = generate_pink_noise(len(audio))
    pink_noise *= np.sqrt(power_noise / np.var(pink_noise))  # Масштабируем по мощности
    
    return np.clip(audio + pink_noise, -1.0, 1.0)