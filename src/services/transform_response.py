from src.config.config import settings
import requests
from typing import Optional, Dict, Any
from src.commons import quizAnswerMapping


class QuizTransform():
    def __init__(self) -> None:
        pass

    def extract_data(self, api: str, id: Optional[int]):
        api = api.format(QUIZ_ID=id)
        response = requests.get(api)
        if response.status_code == 200:
            return response.json().get('data')
        return dict()

    def transform_res(self, res: Dict[Any]):
        transformed_res = {}
        transformed_res['id'] = res.get('id')
        transformed_res['title'] = res.get('attributes').get('name')
        transformed_res['slug'] = None
        transformed_res['examTerm'] = res.get('attributes').get('type').replace('GK2', 'Giữa kỳ II').replace('CK2', 'Cuối kỳ II')
        transformed_res['duration'] = res.get('attributes').get('duration')
        transformed_res['schoolYear'] = res.get('attributes').get('schoolYear')
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
                    'correctLabel': quizAnswerMapping.get(item.get('attributes').get('answer')),
                }
            )

        return transformed_res

    def get_all_filtered_ids(self, api_url: str):
        filtered_ids = []
        res = self.extract_data(api_url, id=None)
        for item in res:
            filtered_ids.append(item.get('id'))
        return filtered_ids
    



# transformed_res = transform_res(extract_data(settings.api_get_quiz_by_id, id=1774))
# print(transformed_res)
# get_all_filtered_ids(settings.api_get_filtered_quiz_ids)