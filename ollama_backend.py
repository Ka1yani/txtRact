"""
Ollama OCR Backend
==================
Calls Ollama's /api/chat vision endpoint with base64-encoded images
using the deepseek-ocr model.
"""

from __future__ import annotations

import base64
import os

import requests

import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class OCRResponse:
    text: str
    source: str

# ── Configuration ───────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL_BASE",  "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_OCR_MODEL", "deepseek-ocr:3b")

HEALTH_CHECK_TIMEOUT = 5       # seconds
INFERENCE_TIMEOUT    = 600     # 10 minutes -- CPU inference is slow

# Prompts tried in order -- first non-empty result wins
PROMPTS = [
    "Extract the text in the image.",
]


class OllamaOCRBackend:
    """Calls Ollama's /api/chat endpoint with base64-encoded images."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
    ):
        self._base_url = base_url
        self._model = model

    @property
    def name(self) -> str:
        return f"Ollama/{self._model}"

    def is_available(self) -> bool:
        try:
            resp = requests.get(
                f"{self._base_url}/",
                timeout=HEALTH_CHECK_TIMEOUT,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def extract_text(self, file_path: str, file_name: str) -> OCRResponse:
        image_b64 = self._encode_image(file_path)
        if not image_b64:
            return OCRResponse(text="", source=self.name)

        for i, prompt in enumerate(PROMPTS, 1):
            label = "grounding" if i == 1 else "simple"
            logger.info(f"[{self.name}] Trying {label} prompt ({i}/{len(PROMPTS)})...")

            text = self._chat(image_b64, prompt)
            if text.strip():
                return OCRResponse(text=text, source=self.name)

            logger.warning(f"[{self.name}] {label.capitalize()} prompt returned empty")

        return OCRResponse(text="", source=self.name)

    def _chat(self, image_b64: str, prompt: str) -> str:
        """Single Ollama /api/chat call with a vision message."""
        payload = {
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }],
            "stream": False,
            "options": {
                "num_ctx": 4096  # Restrict KV cache size to prevent OOM
            }
        }

        try:
            resp = requests.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=INFERENCE_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")

        except requests.ConnectionError:
            logger.error(f"[{self.name}] Cannot connect to {self._base_url}")
        except requests.Timeout:
            logger.error(f"[{self.name}] Timed out (>{INFERENCE_TIMEOUT}s)")
        except Exception as e:
            logger.error(f"[{self.name}] Chat error: {e}")

        return ""

    @staticmethod
    def _encode_image(file_path: str) -> str:
        """Reads an image file and returns its base64-encoded string."""
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"[Ollama] Failed to read image: {e}")
            return ""
