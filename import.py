from database import get_session_from_engine
from sqlalchemy import create_engine
from import_exam_bank_by_exam_id import import_exam_bank
from exam_bank_models import Base
import typer

quizz_database_url = 'postgresql://postgres:3FGae34ggFIg@dica-server:54321/exam_bank'
engine = create_engine(
    quizz_database_url, echo=False,
    pool_size=50,
    max_overflow=0,
)
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("Connection successful:", result.scalar())  # If no error, connection established
except Exception as e:
    print("Connection failed:", e)

Base.metadata.create_all(engine)


def main(src_exam_id: int):
# def main(last_idx: int):
    # with open('id_import_2.txt', 'r') as file:
    #     id_list = []
    #     for line in file:
    #         id = line.strip()
    #         id_list.append(int(id))
    # if last_idx != 0: last_idx += 1
    # idx = 0 + last_idx
    # error = []
    # for id in id_list[last_idx:]:
    #     try:
    #         with get_session_from_engine(engine) as session:
    #             exam_id = import_exam_bank(session, page=id)
    #             print(f'{exam_id}   {idx}')
    #             idx += 1
    #     except:
    #         error.append(id)
    # print(error)
    with get_session_from_engine(engine) as session:
        exam_id = import_exam_bank(session, page=src_exam_id)
        print(exam_id)

if __name__=="__main__":
    typer.run(main)
    # main()