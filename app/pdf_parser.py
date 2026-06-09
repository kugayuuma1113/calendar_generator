"""時間割 PDF から科目データを抽出するパーサ。"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

import pdfplumber

DAYS_OF_WEEK = ["月", "火", "水", "木", "金"]


def parse_timetable_pdf(
    pdf_source: str | Path | bytes | BinaryIO,
    day_page_indices: dict[str, int],
) -> tuple[list[dict], list[str]]:
    """
    PDF から科目データを抽出する（DB には書き込まない）。

    Args:
        pdf_source: ファイルパス、bytes、またはファイルライクオブジェクト
        day_page_indices: 曜日 → 0 始まりのページインデックス（例: {"月": 1} は PDF の 2 ページ目）

    Returns:
        (科目 dict のリスト, 警告メッセージのリスト)
    """
    subjects: list[dict] = []
    warnings: list[str] = []
    seen_keys: set[tuple[str, int | None, str]] = set()

    if isinstance(pdf_source, bytes):
        pdf_source = io.BytesIO(pdf_source)

    with pdfplumber.open(pdf_source) as pdf:
        total_pages = len(pdf.pages)

        for day, page_index in day_page_indices.items():
            if page_index < 0 or page_index >= total_pages:
                warnings.append(
                    f"{day}曜: ページ {page_index + 1} は範囲外です（PDF は全 {total_pages} ページ）"
                )
                continue

            page_subjects, page_warnings = _parse_page(pdf.pages[page_index], day)
            warnings.extend(page_warnings)

            for item in page_subjects:
                key = (item["day"], item["period"], item["code"])
                if key in seen_keys:
                    warnings.append(
                        f"重複: {day}曜 {item['period']}時限 授業コード {item['code']}（{item['name']}）"
                    )
                    continue
                seen_keys.add(key)
                subjects.append(item)

    if not subjects and not any("範囲外" in w for w in warnings):
        warnings.append("抽出された科目が 0 件です。ページ指定または PDF 形式を確認してください。")

    return subjects, warnings


def _parse_page(page, day_of_week: str) -> tuple[list[dict], list[str]]:
    """1 ページ分の表をパースする。"""
    subjects: list[dict] = []
    warnings: list[str] = []

    table = page.extract_table()
    if not table or len(table) < 2:
        warnings.append(f"{day_of_week}曜: 表データを読み取れませんでした")
        return subjects, warnings

    current_period: int | None = None

    for row in table[1:]:
        if not row or len(row) < 8:
            continue

        if "全" not in (row[4] or "") and "実" not in (row[4] or ""):
            continue

        if row[1] is None or not str(row[1]).isdigit():
            continue

        if row[0] is not None and str(row[0]).strip() != "":
            match = re.search(r"\d+", str(row[0]))
            if match:
                current_period = int(match.group())

        if current_period is None:
            warnings.append(
                f"{day_of_week}曜: 時限未確定の行をスキップ（コード {row[1]}）"
            )
            continue

        year_val = 1
        if row[5] is not None:
            year_match = re.search(r"\d+", str(row[5]))
            if year_match:
                year_val = int(year_match.group())

        subjects.append(
            {
                "code": str(row[1]),
                "reg": str(row[2] or "").replace("\n", " "),
                "name": str(row[7] or "").replace("\n", " "),
                "cat": str(row[6] or "").replace("\n", " "),
                "year": year_val,
                "day": day_of_week,
                "period": current_period,
            }
        )

    if not subjects:
        warnings.append(f"{day_of_week}曜: 有効な科目行が 0 件でした")

    return subjects, warnings


def build_day_page_indices_sequential(start_page_1based: int) -> dict[str, int]:
    """開始ページ（1 始まり）から月〜金まで連番でページインデックスを生成する。"""
    start_index = start_page_1based - 1
    return {day: start_index + i for i, day in enumerate(DAYS_OF_WEEK)}


def build_day_page_indices_individual(pages_1based: dict[str, int]) -> dict[str, int]:
    """曜日ごとに指定されたページ番号（1 始まり）からインデックス dict を生成する。"""
    return {day: pages_1based[day] - 1 for day in DAYS_OF_WEEK}


def summarize_subjects(subjects: list[dict]) -> dict:
    """プレビュー用の集計情報を返す。"""
    by_day: dict[str, int] = {day: 0 for day in DAYS_OF_WEEK}
    for s in subjects:
        by_day[s["day"]] = by_day.get(s["day"], 0) + 1
    return {
        "total": len(subjects),
        "by_day": by_day,
    }


def pdf_page_count(pdf_bytes: bytes) -> int:
    """PDF の総ページ数を返す。"""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)
