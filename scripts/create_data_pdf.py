import pdfplumber
import re
from sqlmodel import Session, create_engine, SQLModel
from app.models import Subject
from pathlib import Path

# データベースの設定
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)

def process_timetable_pdf(pdf_path: str, day_of_week: str, page_index: int):
    """
    pdfplumberで抽出した表データから辞書を作成し、データベースに保存する
    """
    SQLModel.metadata.create_all(engine)
    subjects_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # 該当のページを指定（例として2ページ目: index 1）
        page = pdf.pages[page_index]
        table = page.extract_table()
        try:

            current_period = None
        
            # 1行目（インデックス0）はヘッダー（'時限', '授業コード'...）なのでスキップしてループ
            for row in table[1:]:
                # 行が空、またはデータが足りない場合はスキップ
                if not row or len(row) < 8:
                    continue

                #コースが「全」または「実」が含まれていない行はスキップ
                if "全" not in row[4] and "実" not in row[4]:
                    continue
                
                # 授業コード（インデックス1）が空または数字でない行は無効な行としてスキップ
                if row[1] is None or not str(row[1]).isdigit():
                    continue

                # --- 時限（インデックス0）の処理 ---
                # None でなければ新しい時限に突入したと判断し、数値を更新する
                if row[0] is not None and row[0].strip() != '':
                    # '1(1·2)' などから最初の数字だけを抽出
                    match = re.search(r'\d+', row[0])
                    if match:
                        current_period = int(match.group())

                # --- その他のデータの抽出と整形 ---
                code = row[1]
                reg = row[2]
                
                # 配当回生（インデックス5）: '1以上' などから数字だけ抽出
                year_val = None
                if row[5] is not None:
                    year_match = re.search(r'\d+', str(row[5]))
                    if year_match:
                        year_val = int(year_match.group())
                
                cat = row[6]
                name = row[7]

                # 辞書としてリストに追加（改行が含まれている場合はスペースに置換）
                subjects_data.append({
                    "code": code,
                    "reg": reg,
                    "name": str(name).replace('\n', ' '),
                    "cat": str(cat).replace('\n', ' '),
                    "year": year_val,
                    "day": day_of_week,
                    "period": current_period
                })

            # --- データベースへの保存処理 ---
            with Session(engine) as session:
                for data in subjects_data:
                    subject = Subject(**data)
                    session.add(subject)
                
                session.commit()
                print(f"{day_of_week}のデータを{len(subjects_data)}件登録しました。")
        except Exception as e:
            print(f"エラーが発生しました: {e}") 

if __name__ == "__main__":
    days_of_week = ["月", "火", "水", "木", "金"]
    current_dir = Path(__file__).parent
    pdf_file_path = current_dir / 'table.pdf'
    for i, day_of_week in enumerate(days_of_week):
        process_timetable_pdf(pdf_file_path, day_of_week, i+1)