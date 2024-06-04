import json
from src.config.config import settings
from src.database import get_session_from_engine
from src.models.exam_bank_models import QuizQuestion
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.sql import select, update
import argparse

parent_path = "/home/dica/Projects/syvan_projects/test_exam_etl/exam_elt/math_questions_prod/"

list_of_filename = [
    "bio_10_single_quiz.json",
    "bio_11_single_quiz.json",
    "bio_12_single_quiz.json",
    "civedu_10_single_quiz.json",
    "civedu_11_single_quiz.json",
    "civedu_12_single_quiz.json",
    "geo_10_single_quiz.json",
    "geo_11_single_quiz.json",
    "geo_12_single_quiz.json",
    "his_10_single_quiz.json",
    "his_11_single_quiz.json",
    "his_12_single_quiz.json",
]

def main():
    parser = argparse.ArgumentParser(description="Upadate explanations with CLI")
    parser.add_argument('--v', type=int, help='Version of AI explanations')
    args = parser.parse_args()

    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"
    engine = create_engine(
        database_id_mapping_url, echo=False,
        pool_size=50,
        max_overflow=0,
    )

    # metadata = MetaData()

    # table = Table('quiz_question', metadata, autoload_with=engine)

    update_list = []

    with get_session_from_engine(engine) as session:
        for filename in list_of_filename:
            with open(parent_path + filename) as f:
                data = json.load(f)
                for item in data:
                    question_id = item['question_id']
                    for version in item['versions']:
                        if version['version'] == args.v:
                            explanation = version['transformed_ai_explanation']
                            break
                    update_list.append({'id': question_id, 'explanation': explanation})


        # update_list = update_list[:3]
        # ids = [10110000000000457, 10110000000000458, 10110000000000459]
        # for i, value in enumerate(update_list):
        #     value['id'] = ids[i]
        # print(update_list)
        session.bulk_update_mappings(QuizQuestion, update_list)
        session.commit()

if __name__ == '__main__':
    main()