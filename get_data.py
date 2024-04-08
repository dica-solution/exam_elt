from sqlalchemy import create_engine, and_
from src.database import get_sessions_from_engines
from src.models.exam_bank_models import Exam, ExamQuestion, QuizQuestion
from src.config.config import settings
from bs4 import BeautifulSoup
import json

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


with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log):
    # questions = session_import.query(QuizQuestion.id, QuizQuestion.original_text, QuizQuestion.quiz_options, QuizQuestion.explanation
    #                                  ).join(ExamQuestion, ExamQuestion.quiz_question_id==QuizQuestion.id
    #                                  ).join(Exam, Exam.id==ExamQuestion.exam_id
    #                                  ).filter(
    #                                      and_(
    #                                          Exam.grade_id==7,
    #                                          Exam.subject_id==14,
    #                                          QuizQuestion.quiz_options!='',
    #                                          QuizQuestion.explanation!='',
    #                                          QuizQuestion.original_text.not_like('%%src%%'),
    #                                          QuizQuestion.quiz_options.not_like('%%src%%'),
    #                                      )
    #                                  ).order_by(QuizQuestion.id).all()
    questions = session_import.query(QuizQuestion.id, QuizQuestion.quiz_type, QuizQuestion.original_text, QuizQuestion.explanation
                                     ).join(ExamQuestion, ExamQuestion.quiz_question_id==QuizQuestion.id
                                     ).join(Exam, Exam.id==ExamQuestion.exam_id
                                     ).filter(
                                         and_(
                                             Exam.grade_id==9,
                                             Exam.subject_id==14,
                                             QuizQuestion.quiz_type == 3,
                                             QuizQuestion.explanation!='',
                                             QuizQuestion.original_text.not_like('%%src%%'),
                                         )
                                     ).order_by(QuizQuestion.id).all()
    result = []
    for question in questions:
        # question_text, correct_option = combine_with_question(question.original_text, convert_options(question.quiz_options))
        result.append({
            'question_id': question.id,
            'question_type': question.quiz_type,
            'question_text': remove_html_with_beautifulsoup(question.original_text),
            # 'question_text': question_text,
            # 'correct_option': correct_option,
            'explanation': remove_html_with_beautifulsoup(question.explanation),
            'good_explanation': False
        })

    # with open('grad_7_questions.json', 'w') as f:
    #     for res in result:
    #         f.write(json.dumps(res, ensure_ascii=False))
    #         f.write('\n')
    print(f'Number of questions: {len(result)}')
    with open('grade_9_questions.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print('Debugging...')