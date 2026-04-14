from sqlmodel import Session, create_engine, SQLModel
from app.models import Subject  # 上記で定義したモデルをインポート

# SQLiteを使用する例
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)

def create_db_and_subjects():
    # テーブルを作成（まだ存在しない場合）
    SQLModel.metadata.create_all(engine)

    # 追加したいデータのリスト
    subjects_data = [
        {"name": "情報理論", "cat": "固有専門", "year": 2, "day": "月", "period": 1},
        {"name": "計算機構造", "cat": "固有専門", "year": 2, "day": "月", "period": 2},
        # ... 残りの50個
    ]

    with Session(engine) as session:
        for data in subjects_data:
            # 辞書を展開してSubjectインスタンスを作成
            subject = Subject(**data)
            session.add(subject)
        
        session.commit()
        print(f"{len(subjects_data)}件のデータを登録しました。")

if __name__ == "__main__":
    create_db_and_subjects()