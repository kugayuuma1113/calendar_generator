# 時間割Generator

大学の履修科目を管理・表示するための時間割作成 Web アプリです。  
FastAPI + HTMX をバックエンド/フロントエンド通信に使用しています。

---

## 現状の機能

### フロントエンド（`templates/index.html` + `static/style.css`）
- **時間割表の表示** — 月〜金・1〜5時限のグリッドを表示
- **フィルタリング** — 以下の条件で科目を絞り込むボタンを装備
  - 回生：1 / 2 / 3 / 4（排他選択）
  - 科目分野：外国語 / 基礎専門 / 固有専門 / 教養 / 全て（複数選択可）
  - 登録区分：事務室登録 / 抽選 / その他 / 全て（複数選択可）
- **科目追加の準備** — 各コマをクリックすると HTMX 経由でバックエンドへリクエストを送る仕組み（API 実装待ち）

### バックエンド（`main.py`）
| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/` | GET | 時間割ページ（HTML）を返す |
| `/api/subjects` | GET | 科目一覧を回生・分野・区分でフィルタリングして返す |
| `/api/timetable` | POST | 時間割データを JSON ファイルに保存する |
| `/api/timetable/{year}` | GET | 保存済み時間割を回生ごとに取得する |

---

## インストール & 起動方法

### 前提条件
- Python 3.12 以上
- [uv](https://github.com/astral-sh/uv) がインストールされていること

### セットアップ

```bash
# 依存パッケージのインストール
uv sync
```

### 科目データの作成（初回のみ）

科目一覧 PDF から `data/subjects.json` を生成します。

```bash
uv run python -m scripts.create_data_pdf
```

> `data/subjects.json` が存在しない場合、サーバー起動時に自動で空のファイルが作成されます。

### サーバー起動

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

起動後、ブラウザで `http://localhost:8000` を開くと時間割表が表示されます。

---

## プロジェクト構成

```
calendar_generator/
├── main.py               # FastAPI アプリ本体
├── templates/
│   └── index.html        # 時間割ページのテンプレート
├── static/
│   └── style.css         # カスタム CSS
├── data/
│   ├── subjects.json     # 科目マスターデータ
│   └── timetable_*.json  # 保存された時間割（回生ごと）
├── scripts/
│   ├── create_data.py        # データ作成スクリプト
│   └── create_data_pdf.py    # PDF から科目データを生成
└── app/
    └── models.py         # データモデル定義
```
