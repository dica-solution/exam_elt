from src.config.config import settings
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import pandas as pd
import json

engine = create_engine(f"{settings.database_url}{settings.db_destination}")

query = """
	select qq.id , tl.src_exam_id , tl.src_quiz_object_type , tl.src_quiz_question_id , tl.src_quiz_question_group_id  , qq.original_text as question, qq.quiz_options as options, qq.explanation
	from public.quiz_question qq 
	join public.exam_question eq on qq.id = eq.quiz_question_id
	join public.exam e on eq.exam_id = e.id
	join public.tracking_logs tl on qq.id = tl.des_quiz_question_id  
	where qq.original_text != '' 
	and qq.quiz_options != '' 
	and qq.explanation = ''
	and e.subject_id in (14, 17, 5, 11)
    and qq.original_text not like '%%src%%'
	and qq.quiz_options not like '%%src%%'
    order by qq.id;
"""

def remove_html_with_beautifulsoup(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    clean_text = soup.get_text()
    return str(clean_text)

def convert_options(x):
    if isinstance(x, str):
        return json.loads(x)
    else:
        return {}

# def wrap_in_p_tag(content):
#     return f'\n<p>{content}</p>'

def combine_with_question(question, options):
    for option in options:
        # value_opt = wrap_in_p_tag(f"<strong>{option.get('label')}</strong>. {option.get('content')}")
        question = remove_html_with_beautifulsoup(question)
        try:
            value_opt = '\n' + option.get('label') + '. ' + remove_html_with_beautifulsoup(option.get('content'))
        except Exception as e:
            print(e)
            value_opt = ''
        question += value_opt
    return question

df = pd.read_sql_query(query, engine)
df['options'] = df['options'].apply(convert_options)
df['question'] = df.apply(lambda row: combine_with_question(row['question'], row['options']), axis=1)
df.drop(columns=['options'], inplace=True)
df.to_json('question_empty_explanation.json', orient='records', lines=True, force_ascii=False)