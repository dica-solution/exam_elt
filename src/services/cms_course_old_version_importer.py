import json
from typing import Any, Dict, List, Optional, Tuple
from src.models.exam_bank_models_for_course import Course, \
    CourseLecture, Lecture, Theory, TheoryExample, QuizQuestion, \
    QuizCollectionGroup, QuizCollection, Media, Category, Uniqid
from src.commons import ObjectTypeStrMapping, GradeIDMapping, SubjectIDMapping, CourseType, LectureType, TheoryType, MediaType
from src.config.config import get_settings, Settings
from src.services.logger_config import setup_logger
from src.services.checker import check_id_exist
from src.services.process_questions import QuestionProcessor
import requests
import backoff
import re
from sqlalchemy.orm import Session

settings = get_settings()
logger = setup_logger()

logger.info("`cms_course_importer` module is running...")


def retry(func):
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3,
                          on_backoff=lambda details: logger.info(f"Retrying in {details['wait']} seconds..."))
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class CourseParser:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings

    def map_id(self, id: int, map_dict: Dict[int, int]) -> int:
        return map_dict.get(id, 0)
    
    def transform_data(self, text_data: Optional[str]):
        
        if text_data:
            # Replace '&amp;' to '&'
            text_data = text_data.replace('&amp;', '&').replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'").replace('operatorname', 'text')

            # Extracts all substrings that match the given regex pattern and replaces '\[' with '(' and '\]' with ')' in each match.
            pattern = r'<span class="math-tex">\\\[.*?\\\]</span>'
            matches = re.findall(pattern, text_data)

            for match in matches:
                new_match = match.replace('\\[', '\\(').replace('\\]', '\\)')
                text_data = text_data.replace(match, new_match)

            pattern = r'\\overparen\{.*?\}'
            matches = re.findall(pattern, text_data)

            for match in matches:
                # Extract the content inside the braces
                content = match[11:-1]  # 11 is the length of '\overparen{', -1 is to exclude the closing brace
                new_match = '\\text{cung } ' + content
                text_data = text_data.replace(match, new_match)
            
            return text_data
        return text_data

    def extract_id_list(self, data_list: List[Dict[str, Any]]) -> List[int]:
        id_list = []
        for data in data_list:
            id_list.append(int(data.get('id')))        
        return id_list

    def extract_data_dict(self, id: int, type:str, settings: Settings) -> Dict[str, Any]:
        if type == 'course':
            url = settings.api_course_detail.replace('{COURSE_ID}', str(id))
        elif type == 'lecture':
            url = settings.api_lecture_detail.replace('{LECTURE_ID}', str(id))
        elif type == 'type_of_maths':
            url = settings.api_type_of_maths_detail.replace('{TOM_ID}', str(id))
        else:
            print(f'Invalid type: {type}')
            return dict()
        headers = {
            'Authorization': f'Bearer {settings.access_key}'
        }

        logger.info(f"Extracting {type} data")

        @retry
        def get_data(url: str, headers: dict):
            response = requests.get(url, headers=headers)
            logger.info(f"Response status code: {response.status_code}")
            response.raise_for_status()
            return response
        
        try:
            response = get_data(url, headers)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return dict()
        
        return response.json()
    
    def process_course(self, course_data: Dict[str, Any]) -> Course:
        uniqid = self.get_uniqid(ObjectTypeStrMapping[CourseType])
        course = Course(
            id = uniqid,
            created_at = course_data.get('createdAt'),
            updated_at = course_data.get('updatedAt'),
            published_at = course_data.get('publishedAt'),
            title = course_data.get('title'),
            banner_url = course_data.get('bannerUrl', ''),
            description = course_data.get('description', ''),
            description_url = course_data.get('descriptionUrl', ''),
            price = course_data.get('price', 0),
            discount_price = course_data.get('discountPrice', 0),
            lecture_count = len(course_data.get('table_of_contents', [])),
            grade_id = self.map_id(course_data.get('grade').get('id'), GradeIDMapping),
            subject_id = self.map_id(course_data.get('subject').get('id'), SubjectIDMapping),
            category_id = 1, # Course category is always 1
            product_id = course_data.get('productId', '')
        )
        return course
    
    def process_lecture(self, node_data: Dict[str, Any], content_id: int, content_type: str) -> Lecture:
        uniqid = self.get_uniqid(ObjectTypeStrMapping[LectureType])
        lecture_node = Lecture(
            id = uniqid,
            created_at = node_data.get('createdAt'),
            updated_at = node_data.get('updatedAt'),
            title = node_data.get('title', ''),
            content_id = content_id,
            content_type = content_type,
            icon_url = node_data.get('iconUrl', '')
        )
        return lecture_node
    
    def process_course_lecture(self, course_id: int, lecture_id: int, parent_id: int, level: int, is_free: bool, node_type: int, position: int) -> CourseLecture:
        course_lecture = CourseLecture(
            course_id = course_id,
            lecture_id = lecture_id,
            parent_id = parent_id,
            level = level,
            is_free = is_free,
            node_type = node_type,
            position = position
        )
        return course_lecture

    def get_uniqid(self, uniqid_type):
        uniqid = Uniqid(uniqid_type=uniqid_type)
        self.session.add(uniqid)
        self.session.flush()
        uniqid = uniqid.to_uniqid_number()
        return uniqid

    def import_courses(self):
        # course_id_list = self.extract_id_list('course', 0, settings)
        course_id_list = [3] # For test import course `Toán 12`
        if course_id_list:
            for course_idx, course_id in enumerate(course_id_list):
                # Import course
                course_data_dict = self.extract_data_dict(course_id, 'course', settings).get('data')
                course = self.process_course(course_data_dict)
                self.session.add(course)

                course_lecture_position = 0
                
                for chapter_idx, chapter_dict in enumerate(course_data_dict.get('table_of_contents', [])[0:1]):
                    # Import chapter
                    chapter = self.process_lecture(chapter_dict, 0, '')
                    self.session.add(chapter)

                    course_lecture_course_chapter = self.process_course_lecture(course.id, chapter.id, 0, 1, False, 1, course_lecture_position)
                    course_lecture_position += 1
                    self.session.add(course_lecture_course_chapter)


                    for lecture_idx, lecture_dict in enumerate(chapter_dict.get('course_lessons', [])[0:1]):
                        # Import lecture
                        lecture_data_dict = self.extract_data_dict(lecture_dict.get('id'), 'lecture', settings).get('data')
                        lecture = self.process_lecture(lecture_data_dict, 0, '')
                        self.session.add(lecture)

                        # Import course_lecture
                        course_lecture_chapter_lecture = self.process_course_lecture(course.id, lecture.id, course_lecture_course_chapter.id, 2, False, 1, course_lecture_position)
                        course_lecture_position += 1
                        self.session.add(course_lecture_chapter_lecture)

                        for content_idx, content_dict in enumerate(lecture_data_dict.get('content_types', [])):
                            if content_dict.get('__component') == 'course.overview':
                                # Import overview
                                theory = Theory(
                                    id = self.get_uniqid(ObjectTypeStrMapping[TheoryType]),
                                    title=self.transform_data(content_dict.get('title', '')),
                                    original_text=self.transform_data(content_dict.get('content', '')),
                                    parsed_text=self.transform_data(content_dict.get('content', ''))
                                )
                                self.session.add(theory)

                                lecture_lecture_theory = self.process_lecture(content_dict, theory.id, 'theory')
                                self.session.add(lecture_lecture_theory)

                                course_lecture_lecture_theory = self.process_course_lecture(course.id, lecture_lecture_theory.id, course_lecture_chapter_lecture.id, 3, False, 2, course_lecture_position)
                                course_lecture_position += 1
                                self.session.add(course_lecture_lecture_theory)
                            
                            if content_dict.get('__component') == 'course.form':
                                # Import Math type
                                math_type_id_list = self.extract_id_list(content_dict.get('course_forms', []))
                                if math_type_id_list:
                                    for math_type_id in math_type_id_list:

                                        # Import Course Form
                                        math_type_data_dict = self.extract_data_dict(math_type_id, 'type_of_maths', settings).get('data')

                                        lecture_math_type = self.process_lecture(math_type_data_dict, 0, '')
                                        self.session.add(lecture_math_type)

                                        course_lecture_lecture_math_type = self.process_course_lecture(course.id, lecture_math_type.id, course_lecture_chapter_lecture.id, 3, False, 1, course_lecture_position)
                                        course_lecture_position += 1
                                        self.session.add(course_lecture_lecture_math_type)

                                        # Import Guide
                                        guide = Theory(
                                            id = self.get_uniqid(ObjectTypeStrMapping[TheoryType]),
                                            title='',
                                            original_text=self.transform_data(math_type_data_dict.get('guide', '')),
                                            parsed_text=self.transform_data(math_type_data_dict.get('guide', ''))
                                        )
                                        self.session.add(guide)

                                        lecture_math_type_theory = self.process_lecture(math_type_data_dict, guide.id, 'theory')
                                        lecture_math_type_theory.title = 'Phương pháp giải'
                                        self.session.add(lecture_math_type_theory)

                                        course_lecture_math_type_theory = self.process_course_lecture(course.id, lecture_math_type_theory.id, course_lecture_lecture_math_type.id, 4, False, 2, course_lecture_position)
                                        course_lecture_position += 1
                                        self.session.add(course_lecture_math_type_theory)

                                        # Import questions
                                        for question_idx, question_dict in enumerate(math_type_data_dict.get('questions', [])):
                                            if question_dict.get('__component') == 'course.group-quiz':
                                                question_list = question_dict.get('related_quizzes', [])
                                                quiz_type = 'quiz'
                                            
                                            if question_dict.get('__component') == 'course.group-essay':
                                                question_list = question_dict.get('related_essays', [])
                                                quiz_type = 'essay'
                                            
                                            if question_dict.get('__component') == 'course.quiz':
                                                question_list = [question_dict]
                                                quiz_type = 'quiz'
                                                
                                            if question_dict.get('__component') == 'course.essay':
                                                question_list = [question_dict]
                                                quiz_type = 'essay'

                                            if question_dict.get('__component') == 'course.group-example-quiz':
                                                question_list = question_dict.get('related_quizzes', [])
                                                quiz_type = 'quiz'
                                                
                                            if question_dict.get('__component') == 'course.group-example-essay':
                                                question_list = question_dict.get('related_essays', [])
                                                quiz_type = 'essay'
                                            
                                            if question_dict.get('__component') == 'course.example-quiz':
                                                question_list = [question_dict]
                                                quiz_type = 'quiz'
                                                
                                            if question_dict.get('__component') == 'course.example-essay':
                                                question_list = [question_dict]
                                                quiz_type = 'essay'
                                            
                                            if question_dict.get('__component') == 'course.group-practice-quiz':
                                                question_list = question_dict.get('related_quizzes', [])
                                                quiz_type = 'quiz'
                                                
                                            if question_dict.get('__component') == 'course.group-practice-essay':
                                                question_list = question_dict.get('related_essays', [])
                                                quiz_type = 'essay'
                                            
                                            if question_dict.get('__component') == 'course.practice-quiz':
                                                question_list = [question_dict]
                                                quiz_type = 'quiz'
                                                
                                            if question_dict.get('__component') == 'course.practice-essay':
                                                question_list = [question_dict]
                                                quiz_type = 'essay'
                                            
                                            if question_list:
                                                question_processor = QuestionProcessor(self.session, False, 0, 0, question_list, quiz_type, 
                                                                                        question_dict.get('title', ''), 1, course.grade_id, course.subject_id)
                                                quiz_collection_group_id, _ = question_processor.process_questions_old_version()
                                                if quiz_collection_group_id:
                                                    lecture_math_type_quiz_collection_group = self.process_lecture(question_dict, quiz_collection_group_id, 'collection')
                                                    self.session.add(lecture_math_type_quiz_collection_group)

                                                    course_lecture_math_type_quiz_collection_group = self.process_course_lecture(course.id, lecture_math_type_quiz_collection_group.id, course_lecture_lecture_math_type.id, 4, False, 2, course_lecture_position)
                                                    course_lecture_position += 1
                                                    self.session.add(course_lecture_math_type_quiz_collection_group)


                            # Import Practice
                            question_list = []
                            if content_dict.get('__component') == 'course.group-quiz':
                                question_list = content_dict.get('related_quizzes', [])
                                quiz_type = 'quiz'
                            
                            if content_dict.get('__component') == 'course.group-essay':
                                question_list = content_dict.get('related_essays', [])
                                quiz_type = 'essay'

                            if content_dict.get('__component') == 'course.quiz':
                                question_list = [content_dict]
                                quiz_type = 'quiz'
                                
                            if content_dict.get('__component') == 'course.essay':
                                question_list = [content_dict]
                                quiz_type = 'essay'

                            if question_list:
                                question_processor = QuestionProcessor(self.session, True, theory.id, course_lecture_position, question_list, quiz_type, 
                                                                        content_dict.get('title', ''), 1, course.grade_id, course.subject_id)
                                
                                quiz_collection_group_id, _ = question_processor.process_questions_old_version()
                                course_lecture_position += _
                                # if quiz_collection_group_id:
                                #     lecture_lecture_quiz_collection_group = self.process_lecture(content_dict, quiz_collection_group_id, 'collection')
                                #     self.session.add(lecture_lecture_quiz_collection_group)

                                #     course_lecture_lecture_quiz_collection_group = self.process_course_lecture(course.id, lecture_lecture_quiz_collection_group.id, course_lecture_chapter_lecture.id, 3, False, 2, course_lecture_position)
                                #     course_lecture_position += 1
                                #     self.session.add(course_lecture_lecture_quiz_collection_group)
                            
                        self.session.commit()

                print(f"Imported course with id {course.id}")