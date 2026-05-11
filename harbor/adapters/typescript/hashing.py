from __future__ import annotations

import hashlib


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").strip()
    return " ".join(normalized.split())


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_sha256(text: str) -> str:
    return sha256_text(normalize_text(text))
