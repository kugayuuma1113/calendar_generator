"""CLI: scripts/table.pdf から科目マスタを database.db に登録する。"""

from pathlib import Path

from sqlmodel import Session

from app.database import create_db_and_tables, engine
from app.models import Subject
from app.pdf_parser import (
    DAYS_OF_WEEK,
    build_day_page_indices_sequential,
    parse_timetable_pdf,
)

# 月曜=PDF 2 ページ目（1 始まり）から連番
DEFAULT_START_PAGE = 2


def import_subjects_to_db(pdf_path: str | Path, start_page_1based: int = DEFAULT_START_PAGE) -> int:
    """PDF をパースして DB に保存する（既存データは置き換え）。"""
    create_db_and_tables()
    day_indices = build_day_page_indices_sequential(start_page_1based)
    subjects, warnings = parse_timetable_pdf(pdf_path, day_indices)

    for msg in warnings:
        print(f"警告: {msg}")

    if not subjects:
        print("登録する科目がありません。")
        return 0

    from app import crud

    with Session(engine) as session:
        count = crud.replace_all_subjects(session, subjects)
        for day in DAYS_OF_WEEK:
            n = sum(1 for s in subjects if s["day"] == day)
            if n:
                print(f"{day}曜: {n} 件")
        print(f"合計 {count} 件を登録しました。")
        return count


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    pdf_file_path = current_dir / "table.pdf"
    if not pdf_file_path.is_file():
        raise SystemExit(f"PDF が見つかりません: {pdf_file_path}")
    import_subjects_to_db(pdf_file_path)
