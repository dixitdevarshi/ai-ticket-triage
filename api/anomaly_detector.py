import sys
from pathlib import Path
import os

ANOMALY_PROJECT_PATH = os.getenv("ANOMALY_PROJECT_PATH", r"D:\visual-anomaly-detection")
sys.path.append(ANOMALY_PROJECT_PATH)

import torch
import numpy as np
from PIL import Image
from torchvision import transforms

from src.model.extractor import DINOv2Extractor
from src.model.patchcore import PatchCore

_extractor = None
_patchcore_cache = {}

TRANSFORM = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def get_extractor():
    global _extractor
    if _extractor is None:
        _extractor = DINOv2Extractor()
    return _extractor


def get_patchcore(category: str):
    if category not in _patchcore_cache:
        memory_bank_path = f"{ANOMALY_PROJECT_PATH}/artifacts/{category}_memory_bank.pt"
        if not Path(memory_bank_path).exists():
            return None
        extractor = get_extractor()
        patchcore = PatchCore(extractor=extractor)
        patchcore.load(memory_bank_path)
        _patchcore_cache[category] = patchcore
    return _patchcore_cache.get(category)


def run_anomaly_detection(image_bytes: bytes, category: str = "bottle"):
    patchcore = get_patchcore(category)
    if patchcore is None:
        return None

    image = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    tensor = TRANSFORM(image).unsqueeze(0)

    image_score, _ = patchcore.predict(tensor)
    score = float(image_score[0].item())

    return {
        "category_used": category,
        "anomaly_score": score
    }
