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

### バックエンド（`main.py`）
| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/` | GET | 時間割ページ（HTML）を返す |
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

科目データの作成（初回のみ）
scripts/table.pdf（時間割 PDF）を配置し、SQLite データベース database.db に科目データを登録します。

uv run python -m scripts.create_data_pdf
PDF の 2〜6 ページ目がそれぞれ月〜金の時間割表に対応します。
再実行すると重複登録される可能性があるため、初回または DB をリセットした後に実行してください。

scripts/create_data.py を使うと、コード内に定義したサンプル科目データを手動で登録することもできます。

サーバー起動
uv run uvicorn main:app --host 0.0.0.0 --port 8000
起動後、ブラウザで http://localhost:8000 を開くと時間割表が表示されます。

プロジェクト構成（主要ファイル）

calendar_generator/
├── main.py                 # FastAPI アプリ本体
├── index.html              # 旧スタンドアロン版 HTML（現行アプリからは未使用）
├── templates/
│   ├── index.html          # 時間割ページのテンプレート（Jinja2）
│   └── partials/
│       ├── subject_list.html   # 科目一覧（サイドパネル）用テンプレート
│       └── enrolled_cell.html  # 履修済みセル表示用テンプレート
├── static/
│   └── style.css           # カスタム CSS
├── scripts/
│   ├── create_data.py          # サンプル科目データを DB に登録
│   └── create_data_pdf.py      # PDF から科目データを DB に登録
├── app/
│   ├── models.py           # Subject / Enrollment モデル定義
│   ├── database.py         # DB 接続・セッション管理
│   └── crud.py             # 科目・履修に関する DB 操作
└── role.md                 # 各ファイルの役割一覧（このプロジェクト用メモ）