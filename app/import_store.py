"""PDF 取り込みプレビュー用の一時ストア。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

PREVIEW_DIR = Path("data/import_previews")


def _preview_path(token: str) -> Path:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    return PREVIEW_DIR / f"{token}.json"


def save_preview(subjects: list[dict], warnings: list[str]) -> str:
    """パース結果を保存し、取り込みトークンを返す。"""
    token = uuid.uuid4().hex
    payload = {
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "subjects": subjects,
        "warnings": warnings,
    }
    _preview_path(token).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    return token


def load_preview(token: str) -> dict | None:
    """トークンに対応するプレビューデータを読み込む。存在しなければ None。"""
    path = _preview_path(token)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete_preview(token: str) -> None:
    """プレビューデータを削除する。"""
    path = _preview_path(token)
    if path.is_file():
        path.unlink()
