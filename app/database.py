from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def create_db_and_tables() -> None:
    """enrollment テーブルを作成（subject テーブルは既存のため skip_existing 的に動作）"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI の Depends で使うセッションジェネレータ"""
    with Session(engine) as session:
        yield session
