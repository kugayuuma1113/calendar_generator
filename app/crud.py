from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import Enrollment, Subject

REG_OTHER_EXCLUDES = ["事務室登録", "抽選"]


def _apply_subject_filters(
    stmt,
    year: int | None = None,
    cats: list[str] | None = None,
    regs: list[str] | None = None,
):
    if year is not None:
        stmt = stmt.where(Subject.year <= year)
    if cats:
        stmt = stmt.where(Subject.cat.in_(cats))
    if regs:
        direct_regs = [reg for reg in regs if reg != "その他"]
        reg_conditions = []
        if direct_regs:
            reg_conditions.append(Subject.reg.in_(direct_regs))
        if "その他" in regs:
            reg_conditions.append(~Subject.reg.in_(REG_OTHER_EXCLUDES))
        stmt = stmt.where(or_(*reg_conditions))
    return stmt


# ────────────────────────────────────────
# Subject（科目マスター）
# ────────────────────────────────────────

def get_subjects(
    db: Session,
    day: str,
    period: int,
    year: int | None = None,
    cats: list[str] | None = None,
    regs: list[str] | None = None,
) -> list[Subject]:
    """指定した曜日・時限・フィルター条件に合う科目を返す。
    year は「N回生以上が受講可能」を意味するため <= で絞る。"""
    stmt = select(Subject).where(Subject.day == day, Subject.period == period)
    stmt = _apply_subject_filters(stmt, year=year, cats=cats, regs=regs)
    return db.exec(stmt).all()


def count_subjects(db: Session) -> int:
    """科目マスタの件数を返す。"""
    return len(db.exec(select(Subject)).all())


def replace_all_subjects(db: Session, subjects_data: list[dict]) -> int:
    """
    科目マスタを全置換する。履修登録はすべて解除される。
    取り込み確定時に使用する。
    """
    for enrollment in db.exec(select(Enrollment)).all():
        db.delete(enrollment)
    for subject in db.exec(select(Subject)).all():
        db.delete(subject)
    for data in subjects_data:
        db.add(Subject(**data))
    db.commit()
    return len(subjects_data)


def get_all_subjects(
    db: Session,
    year: int | None = None,
    cats: list[str] | None = None,
    regs: list[str] | None = None,
) -> list[Subject]:
    """フィルター条件に合う全科目を返す（フィルターパネル用）。
    year は「N回生以上が受講可能」を意味するため <= で絞る。"""
    stmt = select(Subject)
    stmt = _apply_subject_filters(stmt, year=year, cats=cats, regs=regs)
    return db.exec(stmt).all()


def search_subjects(
    db: Session,
    query: str,
    year: int | None = None,
    cats: list[str] | None = None,
    regs: list[str] | None = None,
) -> list[Subject]:
    """科目名または授業コードで科目を検索する。"""
    normalized_query = query.strip()
    if not normalized_query:
        return []

    stmt = select(Subject).where(
        or_(
            Subject.name.contains(normalized_query),
            Subject.code.contains(normalized_query),
        )
    )
    stmt = _apply_subject_filters(stmt, year=year, cats=cats, regs=regs)
    stmt = stmt.order_by(Subject.day, Subject.period, Subject.code)
    return db.exec(stmt).all()


# ────────────────────────────────────────
# Enrollment（履修登録）
# ────────────────────────────────────────

def get_enrollments(db: Session) -> list[dict]:
    """全履修科目を subject テーブルと JOIN して返す"""
    stmt = select(Enrollment, Subject).where(Enrollment.subject_id == Subject.id)
    rows = db.exec(stmt).all()
    return [
        {
            "enrollment_id": e.id,
            "subject_id": s.id,
            "name": s.name,
            "code": s.code,
            "cat": s.cat,
            "reg": s.reg,
            "year": s.year,
            "day": s.day,
            "period": s.period,
        }
        for e, s in rows
    ]


def add_enrollment(db: Session, subject_id: int) -> dict:
    """
    履修登録する。
    同じコマ（同じ曜日・時限）にすでに登録済みの科目があればエラーを返す。
    """
    # 対象の科目情報を取得
    subject = db.get(Subject, subject_id)
    if not subject:
        raise ValueError(f"subject_id={subject_id} は存在しません")

    # 同コマ重複チェック
    existing = db.exec(
        select(Enrollment, Subject)
        .where(Enrollment.subject_id == Subject.id)
        .where(Subject.day == subject.day)
        .where(Subject.period == subject.period)
    ).first()
    if existing:
        raise ValueError(
            f"{subject.day}曜{subject.period}時限にはすでに「{existing[1].name}」が登録されています"
        )

    # 同一科目の重複チェック
    dup = db.exec(
        select(Enrollment).where(Enrollment.subject_id == subject_id)
    ).first()
    if dup:
        raise ValueError(f"「{subject.name}」はすでに履修登録されています")

    enrollment = Enrollment(subject_id=subject_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return {
        "enrollment_id": enrollment.id,
        "subject_id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "cat": subject.cat,
        "reg": subject.reg,
        "year": subject.year,
        "day": subject.day,
        "period": subject.period,
    }


def delete_enrollment(db: Session, enrollment_id: int) -> bool:
    """履修を解除する。成功したら True、対象が存在しなければ False を返す"""
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        return False
    db.delete(enrollment)
    db.commit()
    return True
