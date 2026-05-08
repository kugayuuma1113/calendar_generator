from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.database import create_db_and_tables, get_session
from app import crud
from sqlmodel import Session

app = FastAPI()

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# 曜日マッピング（URL用 → DB用）
DAY_MAP = {"mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金"}


@app.on_event("startup")
def on_startup():
    """サーバー起動時に enrollment テーブルを作成する"""
    create_db_and_tables()


# ────────────────────────────────────────
# ページ
# ────────────────────────────────────────

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
    subjects = crud.get_subjects(db, day=jp_day, period=period, year=year, cat=cat, reg=reg)
    return templates.TemplateResponse(
        request,
        "partials/subject_list.html",
        {"subjects": subjects, "day": jp_day, "period": period, "day_key": day},
    )


# ────────────────────────────────────────
# 履修登録 API
# ────────────────────────────────────────

@app.get("/api/enrollment", response_class=JSONResponse)
async def list_enrollments(db: Session = Depends(get_session)):
    """履修中の全科目を JSON で返す"""
    return crud.get_enrollments(db)


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
