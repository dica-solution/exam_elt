from sqlalchemy.orm import Session
import requests
from src.services.import_ import ExamParser
from src.config.config import settings
from typing import Any, Dict, List, Optional
from src.commons import QuizAnswerMapping

class ExamParserTransformQuiz(ExamParser):
    def __init__(self, session_import: Session, session_log: Session):
        super().__init__(session_import, session_log)

    def transform_res(self, res):
        transformed_res = {}
        transformed_res['id'] = res.get('id')
        transformed_res['title'] = res.get('attributes').get('name')
        transformed_res['slug'] = None
        transformed_res['examTerm'] = res.get('attributes').get('type').replace('GK2', 'Giữa kỳ II').replace('CK2', 'Cuối kỳ II')
        transformed_res['duration'] = res.get('attributes').get('duration')
        transformed_res['schoolYear'] = res.get('attributes').get('schoolYear') if res.get('attributes').get('schoolYear') is not None else ''
        transformed_res['createdAt'] = res.get('attributes').get('createdAt')
        transformed_res['updatedAt'] = res.get('attributes').get('updatedAt')
        transformed_res['publishedAt'] = res.get('attributes').get('publishedAt')

        grade = res.get('attributes').get('grade').get('data')
        transformed_res['grade'] = {
            'id': grade.get('id'),
            'name': grade.get('attributes').get('name'),
            'slug': grade.get('attributes').get('slug'),
            'createdAt': grade.get('attributes').get('createdAt'),
            'updatedAt': grade.get('attributes').get('updatedAt'),
            'publishedAt': grade.get('attributes').get('publishedAt'),
        }


        subject = res.get('attributes').get('subject').get('data')
        transformed_res['subject'] = {
            'id': subject.get('id'),
            'name': subject.get('attributes').get('name'),
            'slug': subject.get('attributes').get('slug'),
            'createdAt': subject.get('attributes').get('createdAt'),
            'updatedAt': subject.get('attributes').get('updatedAt'),
            'publishedAt': subject.get('attributes').get('publishedAt'),
        }
        transformed_res['school'] = None

        related_items = res.get('attributes').get('questions').get('data')
        transformed_res['relatedItems'] = []
        for item in related_items:
            if len(item.get('attributes').get('Options'))==4:
                transformed_res['relatedItems'].append(
                    {
                        'id': item.get('id'),
                        '__component': 'exam.single-quiz-from-quiz',
                        'title': '',
                        'questionContent': item.get('attributes').get('content'),
                        'shortAnswer': item.get('attributes').get('Explanation'),
                        'longAnswer': item.get('attributes').get('Explanation'),
                        'point': None,
                        'questionAudio': None,
                        'questionImages': None,
                        'labelA': item.get('attributes').get('Options')[0].get('content').replace('<strong>A. </strong>', ''),
                        'labelB': item.get('attributes').get('Options')[1].get('content').replace('<strong>B. </strong>', ''),
                        'labelC': item.get('attributes').get('Options')[2].get('content').replace('<strong>C. </strong>', ''),
                        'labelD': item.get('attributes').get('Options')[3].get('content').replace('<strong>D. </strong>', ''),
                        'correctLabel': QuizAnswerMapping.get(item.get('attributes').get('answer')),
                    }
                )
            if len(item.get('attributes').get('Options'))==2:
                transformed_res['relatedItems'].append(
                    {
                        'id': item.get('id'),
                        '__component': 'exam.single-quiz-from-quiz',
                        'title': '',
                        'questionContent': item.get('attributes').get('content'),
                        'shortAnswer': item.get('attributes').get('Explanation'),
                        'longAnswer': item.get('attributes').get('Explanation'),
                        'point': None,
                        'questionAudio': None,
                        'questionImages': None,
                        'labelA': item.get('attributes').get('Options')[0].get('content').replace('<strong>A. </strong>', ''),
                        'labelB': item.get('attributes').get('Options')[1].get('content').replace('<strong>B. </strong>', ''),
                        'correctLabel': QuizAnswerMapping.get(item.get('attributes').get('answer')),
                    }
                )

        return transformed_res
    
    
    def extract_data(self, exam_id):
        url = settings.api_get_quiz_by_id.format(QUIZ_ID=exam_id)
        response = requests.get(url)
        if response.status_code == 200:
            return self.transform_res(res=response.json().get('data'))
        return dict()
    
def get_all_filtered_ids(api_url: str):
    filtered_ids = []
    res = requests.get(api_url).json().get('data')
    for item in res:
        filtered_ids.append(item.get('id'))
    return filtered_ids


def import_exam_bank(session_import: Session, session_log: Session, quiz_id: int):
    quiz_importer = ExamParserTransformQuiz(session_import, session_log)
    exam_id = quiz_importer.import_exam(quiz_id)
    return exam_id