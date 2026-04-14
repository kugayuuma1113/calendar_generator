from sqlmodel import Field, SQLModel

class Subject(SQLModel, table=True):
    # IDは自動採番されるため、作成時はNoneを許容
    id: int | None = Field(default=None, primary_key=True)
    name: str
    cat: str          # 教養, 固有専門, 共通専門
    year: int         # 何回生か
    day: str          # 曜日
    period: int       # 時限