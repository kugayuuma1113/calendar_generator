## 時間割Generator

大学の履修科目を管理・表示するための時間割作成 Web アプリです。  
FastAPI + HTMX + SQLite（SQLModel）を使用しています。

---

## 現状の機能

### フロントエンド（`templates/index.html` + `static/style.css`）
- **時間割表の表示**: 月〜金・1〜5時限のグリッドを表示
- **フィルタリング**: 以下の条件で科目を絞り込み
  - 回生：1 / 2 / 3 / 4（排他選択）
  - 科目分野：外国語 / 基礎専門 / 固有専門 / 教養 / 全て（複数選択可）
  - 登録区分：事務室登録 / 抽選 / その他 / 全て（複数選択可）
- **履修登録**: 各コマをクリックすると科目一覧が表示され、履修登録・解除ができる
- **PDF 取り込み**（`/import`）: 時間割 PDF をアップロードし、プレビュー確認後に科目マスタを登録

### バックエンド（`main.py`）
| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/` | GET | 時間割ページ（HTML）を返す |
| `/import` | GET | PDF 取り込みページ |
| `/api/import/preview` | POST | PDF をパースしプレビュー HTML を返す |
| `/api/import/confirm` | POST | プレビュー内容で科目マスタを全置換 |
| `/api/import/cancel` | POST | プレビューを破棄 |
| `/api/subjects/{day}/{period}` | GET | 指定コマの科目一覧を HTML フラグメントで返す |
| `/api/enrollment` | GET | 履修中の全科目を JSON で返す |
| `/api/enrollment` | POST | 履修登録する |
| `/api/enrollment/{enrollment_id}` | DELETE | 履修解除する |

---

## インストール & 起動方法

### 前提条件
- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv) がインストールされていること

### セットアップ

```bash
# 依存パッケージのインストール
uv sync

# サーバー起動
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

起動後、ブラウザで http://localhost:8000 を開くと時間割表が表示されます。

### 科目データの登録

**Web から（推奨）**

1. http://localhost:8000/import を開く
2. 時間割 PDF をアップロード
3. ページ指定（月曜の開始ページから連番、または曜日ごとに指定）
4. プレビューで内容を確認し「取り込みを確定」

確定時は既存の科目マスタを**すべて置き換え**、履修登録も**すべて解除**されます。

**CLI から（従来どおり）**

`scripts/table.pdf` を配置して実行します（Web 取り込みと同じパーサを使用、既存データは置き換え）。

```bash
uv run python -m scripts.create_data_pdf
```

PDF の 2〜6 ページ目がそれぞれ月〜金に対応する想定です（開始ページ 2）。

`scripts/create_data.py` ではサンプル科目を手動登録できます。

---

## プロジェクト構成（主要ファイル）

```
calendar_generator/
├── main.py                 # FastAPI アプリ本体
├── templates/
│   ├── index.html          # 時間割ページ
│   ├── import.html         # PDF 取り込みページ
│   └── partials/
│       ├── subject_list.html
│       ├── enrolled_cell.html
│       ├── import_preview.html
│       └── import_success.html
├── static/style.css
├── app/
│   ├── models.py
│   ├── database.py
│   ├── crud.py
│   ├── pdf_parser.py       # PDF パース（Web / CLI 共通）
│   └── import_store.py     # プレビュー一時保存
├── scripts/
│   ├── create_data.py
│   └── create_data_pdf.py
└── data/import_previews/   # プレビュー用（git 管理外）
```
