from sqlmodel import Field, SQLModel


class Subject(SQLModel, table=True):
    # IDは自動採番されるため、作成時はNoneを許容
    id: int | None = Field(default=None, primary_key=True)
    code: str
    reg: str          # 登録区分
    name: str
    cat: str          # 分野（外国語, 基礎専門, 固有専門, 教養など）
    year: int         # 何回生か
    day: str          # 曜日（月火水木金）
    period: int       # 時限（1〜5）


class Enrollment(SQLModel, table=True):
    """ユーザーが履修登録した科目"""
    id: int | None = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")