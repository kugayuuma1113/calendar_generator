## ファイルの役割一覧

### ルートディレクトリ
- **`main.py`**: FastAPI アプリ本体。テンプレートや静的ファイルの設定、エンドポイント定義、DB セッションの依存関係など、Web アプリのエントリーポイント。
- **`index.html`**: 旧構成のスタンドアロン版フロントエンド HTML。FastAPI からは参照されておらず、現行動作には不要（デザインや構成の参考用）。
- **`README.md`**: プロジェクトの説明・セットアップ手順・機能概要をまとめたドキュメント。
- **`pyproject.toml`**: パッケージ管理・依存関係・Python バージョンなどのプロジェクト設定。
- **`uv.lock`**: `uv` による依存関係のロックファイル。インストールされるパッケージのバージョンを固定する。
- **`.gitignore`**: Git 管理から除外するファイル・ディレクトリ（`*.db`, `*.pdf`, 仮想環境など）を定義する。
- **`.python-version`**: 使用する Python バージョンを指定するためのファイル（pyenv などで利用）。

### `app/` ディレクトリ
- **`app/models.py`**: SQLModel による DB モデル定義。科目マスター `Subject` と履修情報 `Enrollment` のテーブルを表す。
- **`app/database.py`**: SQLite DB への接続設定と、テーブル作成関数・FastAPI 用セッション依存関数を提供。
- **`app/crud.py`**: DB アクセスロジックを集約したモジュール。科目取得、科目一覧取得、履修登録・解除などの操作を行う。

### `templates/` ディレクトリ
- **`templates/index.html`**: メインの時間割ページの Jinja2 テンプレート。フィルター UI・時間割グリッド・履修済み表示・サイドパネルなど、現在の画面構成の中心。
- **`templates/partials/subject_list.html`**: 指定コマの科目一覧を表示する部分テンプレート。HTMX 経由で `/api/subjects/{day}/{period}` から読み込まれる。
- **`templates/partials/enrolled_cell.html`**: 履修登録後のセル表示用部分テンプレート。HTMX 経由で `/api/enrollment` に POST した結果として使用される。

### `static/` ディレクトリ
- **`static/style.css`**: Tailwind CSS によるスタイルに加えて、時間割表やカード、サイドパネルなどのカスタムスタイルを定義。

### `scripts/` ディレクトリ
- **`scripts/create_data_pdf.py`**: `scripts/table.pdf` から時間割表を読み取り、曜日・時限ごとにパースして `database.db` の `subject` テーブルへ科目データを一括登録するスクリプト。
- **`scripts/create_data.py`**: Python コード内に定義したサンプル科目データを `database.db` の `subject` テーブルへ登録するための小さなユーティリティスクリプト。
- **`scripts/table.pdf`**（Git 管理外・実ファイル想定）: 大学の時間割が掲載された元 PDF。`create_data_pdf.py` の入力として使用する。

### その他
- **`data/subjects.json`**（現状は空・未使用）: 旧設計では科目マスターデータ JSON を置く想定だったが、現行コードからは参照されていない。動作には不要（削除してもアプリには影響しない）。

