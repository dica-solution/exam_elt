from sqlalchemy import create_engine, and_, desc
from src.database import get_sessions_from_engines
from src.models.exam_bank_models import Exam, ExamQuestion, QuizQuestion, TrackingLogs
from src.config.config import settings
from bs4 import BeautifulSoup
import json
import argparse

def create_and_check_engine(database_url, echo=False, pool_size=50, max_overflow=0):
    try:
        engine = create_engine(
            database_url, echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        with engine.connect() as connection:
            print("Connection successful!")   
            return engine
    except Exception as e:
        print(f"Connection failed: {e}")
        return None 
    
database_destination_url = f"{settings.database_url}{settings.db_destination}"
database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"    

engine_import = create_and_check_engine(database_url=database_destination_url)
engine_log = create_and_check_engine(database_url=database_id_mapping_url)

def remove_html_with_beautifulsoup(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    clean_text = soup.get_text()
    return str(clean_text)

def convert_options(x):
    if isinstance(x, str):
        return json.loads(x)
    else:
        return {}
    
def combine_with_question(question, options):
    question = remove_html_with_beautifulsoup(question)
    correct_option = ''
    for option in options:        
        try:
            value_opt = '\n' + option.get('label') + '. ' + remove_html_with_beautifulsoup(option.get('content'))
            if option.get('is_correct'):
                correct_option = option.get('label')
        except Exception as e:
            print(e)
            value_opt = ''
        question += value_opt
    return question, correct_option

def get_correct_option(options):
    opt = ""
    correct_opt = ""
    for option in options:
        opt += option.get('label') + '. ' + remove_html_with_beautifulsoup(option.get('content')) + '\n'
        if option.get('is_correct'):
            correct_opt= option.get('label')
    return opt, correct_opt

def main():
    parser = argparse.ArgumentParser(description="Get data with CLI")
    parser.add_argument('--c', type=int, help='Grade id')
    parser.add_argument('--file', type=str, help='Path save file')
    args = parser.parse_args()

    with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log):
        questions = session_import.query(QuizQuestion.id, QuizQuestion.quiz_type, QuizQuestion.original_text, QuizQuestion.quiz_options, QuizQuestion.explanation
                                        ).join(ExamQuestion, ExamQuestion.quiz_question_id==QuizQuestion.id
                                        ).join(Exam, Exam.id==ExamQuestion.exam_id
                                        ).filter(
                                            and_(
                                                Exam.grade_id==args.c,
                                                Exam.subject_id==14,
                                                QuizQuestion.quiz_type == 1,
                                                #  QuizQuestion.explanation!='',
                                                QuizQuestion.original_text.not_like('%%src%%'),
                                                QuizQuestion.explanation.not_like('%%src%%'),
                                            )
                                        ).order_by(QuizQuestion.id).all()
        


        result = []
        for question in questions:
            try:
                options, correct_option = get_correct_option(convert_options(question.quiz_options))
                result.append({
                    'question_id': question.id,
                    'original_text': remove_html_with_beautifulsoup(question.original_text),
                    'quiz_options': options,
                    'correct_option': correct_option,
                    'original_explanation': remove_html_with_beautifulsoup(question.explanation) if question.explanation else '',

                })
            except:
                print(f'Error: {question.id}')

        print(f'Number of questions: {len(result)}')
        with open(args.file, 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()