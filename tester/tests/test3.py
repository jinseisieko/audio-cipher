import numpy as np

def f(audio: np.ndarray, snr_db: float = 20.0) -> np.ndarray:
    """Add white noise to achieve the given SNR (dB)."""
    power_signal = np.mean(audio ** 2)
    power_noise = power_signal / (10 ** (snr_db / 10))
    noise = np.random.normal(0.0, np.sqrt(power_noise), size=audio.shape).astype(np.float32)
    return np.clip(audio + noise, -1.0, 1.0)
