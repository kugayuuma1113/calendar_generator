from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app import crud, import_store
from app.database import create_db_and_tables, get_session
from app.pdf_parser import (
    DAYS_OF_WEEK,
    build_day_page_indices_individual,
    build_day_page_indices_sequential,
    parse_timetable_pdf,
    summarize_subjects,
)

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB

app = FastAPI()

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# 曜日マッピング（URL用 → DB用）
DAY_MAP = {"mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金"}
REVERSE_DAY_MAP = {value: key for key, value in DAY_MAP.items()}
DAY_ORDER = ["月", "火", "水", "木", "金"]


def parse_multi_value(value: str | None) -> list[str] | None:
    if not value:
        return None
    values = [item.strip() for item in value.split(",") if item.strip()]
    return values or None


def build_enrollment_summary(enrollments: list[dict]) -> dict:
    by_cat: dict[str, int] = {}
    by_reg: dict[str, int] = {}
    by_day: dict[str, int] = {day: 0 for day in DAY_ORDER}

    for enrollment in enrollments:
        cat = enrollment["cat"] or "未分類"
        reg = enrollment["reg"] or "その他"
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_reg[reg] = by_reg.get(reg, 0) + 1
        if enrollment["day"] in by_day:
            by_day[enrollment["day"]] += 1

    return {
        "total": len(enrollments),
        "by_cat": by_cat,
        "by_reg": by_reg,
        "by_day": by_day,
    }


@app.on_event("startup")
def on_startup():
    """サーバー起動時に enrollment テーブルを作成する"""
    create_db_and_tables()


# ────────────────────────────────────────
# ページ
# ────────────────────────────────────────


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request, db: Session = Depends(get_session)):
    """PDF 取り込みページ"""
    enrollments = crud.get_enrollments(db)
    return templates.TemplateResponse(
        request,
        "import.html",
        {
            "subject_count": crud.count_subjects(db),
            "enrollment_count": len(enrollments),
        },
    )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_session)):
    """時間割ページを表示。履修済み科目をテンプレートに渡す"""
    enrollments = crud.get_enrollments(db)
    # {(day, period): enrollment_dict} の辞書に変換して Jinja2 で参照しやすくする
    enrolled_map = {(e["day"], e["period"]): e for e in enrollments}
    return templates.TemplateResponse(
        request,
        "index.html",
        {"enrolled_map": enrolled_map},
    )


# ────────────────────────────────────────
# 科目一覧（セルクリック時）
# ────────────────────────────────────────


@app.get("/api/subjects/{day}/{period}", response_class=HTMLResponse)
async def get_subjects_for_cell(
    request: Request,
    day: str,
    period: int,
    year: Optional[int] = 1,
    cat: Optional[str] = None,
    reg: Optional[str] = None,
    db: Session = Depends(get_session),
):
    """
    指定コマ（曜日・時限）の科目一覧を HTML フラグメントで返す。
    HTMX がセルクリックで呼び出し、右パネルに差し込む。
    """
    jp_day = DAY_MAP.get(day, day)
    cats = parse_multi_value(cat)
    regs = parse_multi_value(reg)
    subjects = crud.get_subjects(
        db, day=jp_day, period=period, year=year, cats=cats, regs=regs
    )
    return templates.TemplateResponse(
        request,
        "partials/subject_list.html",
        {"subjects": subjects, "day": jp_day, "period": period, "day_key": day},
    )


@app.get("/api/subjects/search", response_class=HTMLResponse)
async def search_subjects(
    request: Request,
    q: str = "",
    year: Optional[int] = 1,
    cat: Optional[str] = None,
    reg: Optional[str] = None,
    db: Session = Depends(get_session),
):
    """科目名・授業コードで科目を検索し、HTML フラグメントで返す。"""
    query = q.strip()
    subjects = crud.search_subjects(
        db,
        query=query,
        year=year,
        cats=parse_multi_value(cat),
        regs=parse_multi_value(reg),
    )
    return templates.TemplateResponse(
        request,
        "partials/search_results.html",
        {
            "subjects": subjects,
            "query": query,
            "day_key_map": REVERSE_DAY_MAP,
        },
    )


# ────────────────────────────────────────
# 履修登録 API
# ────────────────────────────────────────


@app.get("/api/enrollment", response_class=JSONResponse)
async def list_enrollments(db: Session = Depends(get_session)):
    """履修中の全科目を JSON で返す"""
    return crud.get_enrollments(db)


@app.get("/api/enrollment/summary", response_class=HTMLResponse)
async def enrollment_summary(request: Request, db: Session = Depends(get_session)):
    """履修一覧とサマリーを HTML フラグメントで返す"""
    enrollments = crud.get_enrollments(db)
    enrollments.sort(
        key=lambda e: (
            DAY_ORDER.index(e["day"]) if e["day"] in DAY_ORDER else len(DAY_ORDER),
            e["period"],
            e["code"],
        )
    )
    return templates.TemplateResponse(
        request,
        "partials/enrollment_summary.html",
        {
            "enrollments": enrollments,
            "summary": build_enrollment_summary(enrollments),
            "day_key_map": REVERSE_DAY_MAP,
        },
    )


@app.post("/api/enrollment", response_class=HTMLResponse)
async def add_enrollment(
    request: Request,
    subject_id: int = Form(...),
    db: Session = Depends(get_session),
):
    """
    履修登録する。成功時はセル更新用の HTML フラグメントを返す。
    同一コマに2科目登録しようとするとエラーメッセージを返す。
    """
    try:
        enrolled = crud.add_enrollment(db, subject_id)
        return templates.TemplateResponse(
            request,
            "partials/enrolled_cell.html",
            {"enrolled": enrolled},
        )
    except ValueError as e:
        return HTMLResponse(
            content=f'<p class="text-red-400 text-sm p-2">{e}</p>',
            status_code=400,
        )


# ────────────────────────────────────────
# PDF 取り込み（Phase 1）
# ────────────────────────────────────────


@app.post("/api/import/preview", response_class=HTMLResponse)
async def import_preview(
    request: Request,
    pdf_file: UploadFile = File(...),
    page_mode: str = Form("sequential"),
    start_page: int = Form(2),
):
    """PDF をパースしてプレビュー HTML を返す（DB は更新しない）"""
    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        return HTMLResponse(
            '<p class="text-red-400 text-sm p-4">PDF ファイルを選択してください。</p>',
            status_code=400,
        )

    content = await pdf_file.read()
    if len(content) > MAX_PDF_BYTES:
        return HTMLResponse(
            '<p class="text-red-400 text-sm p-4">ファイルサイズが大きすぎます（上限 20MB）。</p>',
            status_code=400,
        )

    form = await request.form()
    try:
        if page_mode == "individual":
            pages_1based: dict[str, int] = {}
            for day in DAYS_OF_WEEK:
                raw = form.get(f"page_{day}")
                if raw is None or str(raw).strip() == "":
                    return HTMLResponse(
                        f'<p class="text-red-400 text-sm p-4">{day}曜のページ番号を入力してください。</p>',
                        status_code=400,
                    )
                pages_1based[day] = int(raw)
            day_indices = build_day_page_indices_individual(pages_1based)
        else:
            day_indices = build_day_page_indices_sequential(int(start_page))
    except ValueError:
        return HTMLResponse(
            '<p class="text-red-400 text-sm p-4">ページ番号は正の整数で指定してください。</p>',
            status_code=400,
        )

    try:
        subjects, warnings = parse_timetable_pdf(content, day_indices)
    except Exception as e:
        return HTMLResponse(
            f'<p class="text-red-400 text-sm p-4">PDF の読み取りに失敗しました: {e}</p>',
            status_code=400,
        )

    import_token = import_store.save_preview(subjects, warnings)
    summary = summarize_subjects(subjects)

    return templates.TemplateResponse(
        request,
        "partials/import_preview.html",
        {
            "import_token": import_token,
            "subjects": subjects,
            "warnings": warnings,
            "summary": summary,
        },
    )


@app.post("/api/import/confirm", response_class=HTMLResponse)
async def import_confirm(
    request: Request,
    import_token: str = Form(...),
    db: Session = Depends(get_session),
):
    """プレビュー済みデータを DB に反映する"""
    preview = import_store.load_preview(import_token)
    if preview is None:
        return HTMLResponse(
            '<p class="text-red-400 text-sm p-4">プレビューの有効期限が切れたか、既に処理済みです。再度プレビューしてください。</p>',
            status_code=400,
        )

    if not preview.get("subjects"):
        import_store.delete_preview(import_token)
        return HTMLResponse(
            '<p class="text-red-400 text-sm p-4">登録する科目がありません。</p>',
            status_code=400,
        )

    cleared_enrollments = len(crud.get_enrollments(db))
    count = crud.replace_all_subjects(db, preview["subjects"])
    import_store.delete_preview(import_token)

    return templates.TemplateResponse(
        request,
        "partials/import_success.html",
        {"count": count, "cleared_enrollments": cleared_enrollments},
    )


@app.post("/api/import/cancel", response_class=HTMLResponse)
async def import_cancel(import_token: str = Form(...)):
    """プレビューを破棄する"""
    import_store.delete_preview(import_token)
    return HTMLResponse(
        '<p class="text-sm text-muted text-center py-8">プレビューをキャンセルしました。'
        "再度 PDF をアップロードしてください。</p>"
    )


@app.delete("/api/enrollment/{enrollment_id}", response_class=HTMLResponse)
async def remove_enrollment(
    request: Request,
    enrollment_id: int,
    db: Session = Depends(get_session),
):
    """履修解除する。成功時は空のセル HTML を返す"""
    ok = crud.delete_enrollment(db, enrollment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    # 空のセルを返して HTMX がセルを上書きする
    return HTMLResponse(content='<div class="add-icon">＋</div>', status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
