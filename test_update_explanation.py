from src.config.config import settings
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker

engine = create_engine(f'{settings.database_url}{settings.db_dev_quiz}')
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData()

single_quiz_table = Table('components_exam_single_quizs', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String),
    Column('question_content', Text),
    Column('short_answer', Text),
    Column('long_answer', Text),
    Column('point', Integer),
    Column('question_audio', Text),
    Column('label_a', Text),
    Column('label_b', Text),
    Column('label_c', Text),
    Column('label_d', Text),
    Column('correct_label', Text),
    metadata, autoload_with=engine
)


records = []

question_with_explantion_filename = "grade_7_question_with_explantion.json"
with open(question_with_explantion_filename, 'r') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['explanation'] != '':
            records.append({'id': record['src_quiz_question_id'], 'long_answer': record['explanation'], 'src_exam_id': record['src_exam_id']})
            # records.append(int(record['src_exam_id']))

exam_id = []

for record in records:
    exam_id.append(int(record['src_exam_id']))
    session.query(single_quiz_table).filter(single_quiz_table.c.id == record['id']).update({single_quiz_table.c.long_answer: record['long_answer']}, synchronize_session=False)
session.commit()

print(set(exam_id))