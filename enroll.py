"""
JARVIS Voice Enrollment
========================
Records 3 voice samples and builds a robust averaged voice profile.
Run this once before starting the assistant.
"""

import os
import sys
import time
import torch
import soundfile as sf
import sounddevice as sd
import numpy as np

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from speechbrain.inference.speaker import EncoderClassifier

SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_FILE = os.path.join(SCRIPT_DIR, "user_embedding.pt")
SAMPLE_RATE    = 16000
DURATION       = 6      # seconds per sample
NUM_SAMPLES    = 3

PROMPTS = [
    'Say: "Hello Jarvis, activate assistant and open YouTube."',
    'Say: "Jarvis, what is the time? Play music and check weather."',
    'Say: "Hey Jarvis, I am the authorized user. Search Google for news."',
]


def record_audio(duration: int, rate: int) -> np.ndarray:
    audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def extract_embedding(audio: np.ndarray, rate: int, classifier, tmp: str) -> torch.Tensor:
    sf.write(tmp, audio, rate)
    data, fs = sf.read(tmp)
    if data.ndim > 1:
        data = data.mean(axis=1)
    signal = torch.tensor(data, dtype=torch.float32).unsqueeze(0)
    if fs != 16000:
        import torchaudio.transforms as T
        signal = T.Resample(orig_freq=fs, new_freq=16000)(signal)
    return classifier.encode_batch(signal).squeeze()


def main():
    print("=" * 50)
    print("       JARVIS Voice Enrollment")
    print("=" * 50)
    print(f"\nWe will record {NUM_SAMPLES} samples ({DURATION}s each).")
    print("Speak naturally and clearly.\n")

    print("Loading voice model...")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": "cpu"}
    )
    print("Model ready.\n")

    tmp = os.path.join(SCRIPT_DIR, ".enroll_tmp.wav")
    embeddings = []

    for i in range(NUM_SAMPLES):
        print(f"--- Sample {i + 1} of {NUM_SAMPLES} ---")
        print(PROMPTS[i])
        for c in range(3, 0, -1):
            print(f"  {c}...")
            time.sleep(1)
        print("  >>> SPEAK NOW <<<")
        audio = record_audio(DURATION, SAMPLE_RATE)
        print(f"  Sample {i + 1} recorded.\n")
        embeddings.append(extract_embedding(audio, SAMPLE_RATE, classifier, tmp))
        time.sleep(0.5)

    print("Building voice profile...")
    averaged = torch.stack(embeddings).mean(dim=0)
    averaged = torch.nn.functional.normalize(averaged, dim=0)
    torch.save(averaged, EMBEDDING_FILE)

    if os.path.exists(tmp):
        os.remove(tmp)

    print(f"Voice profile saved: {EMBEDDING_FILE}")
    print("\nDone! Run assistant.py to start JARVIS.")
    print("=" * 50)


if __name__ == "__main__":
    main()
