import json
import re
import backoff
import requests
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import update
from src.models.exam_bank_models import Uniqid, QuizCollectionGroup, QuizCollection, TheoryExample, QuizQuestion, QuizQuestionGroup, Course, Lecture, \
    Theory, CourseLecture, Media, CourseIDMapping
from src.commons import *
from src.config.config import Settings
from src.services.logger_config import setup_logger
# from src.services.utils import Utils
from src.services.import_exam import ImportExam

logger = setup_logger()

def retry(func):
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3,
                          on_backoff=lambda details: logger.info(f"Retrying in {details['wait']} seconds..."))
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


class Processor:
    def __init__(self, session_import: Session, session_log: Session, settings: Settings):
        self.session = session_import
        self.settings = settings
        self.exam_importer = ImportExam(session_import, session_log, settings)
    
    def _get_mapped_id(self, id: int, mapped_dict: Dict[int, int]) -> int:
        return mapped_dict.get(id, 0)

    def _get_uniqid(self, uniqid_type: int) -> int:
        uniqid = Uniqid(uniqid_type=uniqid_type)
        self.session.add(uniqid)
        self.session.flush()
        return uniqid.to_uniqid_number()

    def _process_level(self, level) -> int:
        if not level:  
            return 0

        level_id = level[0].get('id')
        return {6: 1, 7: 2, 8: 3, 9: 4}.get(level_id, 0)

        
    def _process_links(self, question_audio: str, guide_videos: List[Dict[str, Any]], question_images: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        links = {"audio_links": [], "video_links": [], "image_links": []}
        if question_audio:
            links["audio_links"].append(question_audio)
        if guide_videos:
            for video in guide_videos:
                links["video_links"].append(video.get('url'))
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))

        return links

    def process_course(self, course_data: Dict[str, Any]) -> Course:
        uniqid = self._get_uniqid(ObjectTypeStrMapping[CourseType])
        course = Course(
            id = uniqid,
            created_at = course_data.get('createdAt'),
            updated_at = course_data.get('updatedAt'),
            # published_at = course_data.get('publishedAt'), # unpublish course
            title = course_data.get('title'),
            description = course_data.get('description'),
            grade_id = self._get_mapped_id(course_data.get('grade').get('id'), GradeIDMapping),
            subject_id = self._get_mapped_id(course_data.get('subject').get('id'), SubjectIDMapping),
            lecture_count = len(course_data.get('table_of_contents')),
            category_id = 1
        )

        return course
    
    def process_lecture(self, lecture_data: Dict[str, Any], content_id: int, content_type: str) -> Lecture:
        uniqid = self._get_uniqid(ObjectTypeStrMapping[LectureType])
        lecture = Lecture(
            id = uniqid,
            created_at = lecture_data.get('createdAt'),
            updated_at = lecture_data.get('updatedAt'),
            title = lecture_data.get('title'),
            content_id = content_id,
            content_type = content_type
        )

        return lecture
    
    def process_course_lecture(self, course_id: int, lecture_id: int, parent_id: int, level: int, is_free: bool,node_type: int, position: int):
        course_lecture = CourseLecture(
            course_id = course_id,
            lecture_id = lecture_id,
            parent_id = parent_id,
            level = level,
            is_free = is_free,
            node_type = node_type,
            position = position
        )
        position += 1

        return course_lecture, position
    
    def transform_text(self, text_data: str):
        
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

    def get_data_dict(self, id: int, type: str) -> Dict[str, Any]:
        if type == 'course':
            url = self.settings.api_course_detail.replace('{COURSE_ID}', str(id))
        elif type == 'lecture':
            url = self.settings.api_lecture_detail.replace('{LECTURE_ID}', str(id))
        elif type == 'math_type':
            url = self.settings.api_type_of_maths_detail.replace('{TYPE_ID}', str(id))
        elif type == 'quiz_collection':
            url = self.settings.api_question_collection_detail.replace('{QUESTION_GROUP_ID}', str(id))
        elif type == 'paper_exam_collection':
            url = self.settings.api_paper_exam_collection_detail.replace('{PAPER_EXAM_COLLECTION_ID}', str(id))
        else:
            logger.error(f'Invalid type: {type}')
        
        headers = {
            'Authorization': f'Bearer {self.settings.access_key}'
        }
        logger.info(f"Extracting {type} data.")

        @retry
        def get_data(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
            response = requests.get(url, headers=headers)
            logger.info(f"Status code: {response.status_code}")
            response.raise_for_status()
            return response.json().get('data')
        try:
            response = get_data(url, headers)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            return dict()
        
        return response

    def process_theory(self, theory_data: Dict[str, Any]) -> Theory:
        uniqid = self._get_uniqid(ObjectTypeStrMapping[TheoryType])
        theory = Theory(
            id = uniqid,
            title = self.transform_text(theory_data.get('title')),
            original_text = self.transform_text(theory_data.get('content')),
            parsed_text = self.transform_text(theory_data.get('content'))
        )
        return theory

    def _is_question_existed(self, original_question_id: int):
        flag = self.session.query(CourseIDMapping).filter(CourseIDMapping.original_id == original_question_id,
                                                           CourseIDMapping.entity_type == 'question').first()
        if flag is not None:
            question = self.session.query(QuizQuestion).filter(QuizQuestion.id == flag.new_id).first()
            if question is not None:
                return question, True
            else:
                return None, False
            # return self.session.query(QuizQuestion).filter(QuizQuestion.id == flag.new_id).first(), True
        return None, False

    def _process_quiz(self, question_dict: Dict[str, Any], question_group_id: int):
        original_question_id = question_dict.get('id')
        question, is_existed = self._is_question_existed(original_question_id)
        if is_existed:
            return question, original_question_id, is_existed
        else:
            original_text = self.transform_text(question_dict.get('question_content'))
            parsed_text = original_text
            quiz_type = QuizTypeSingleChoice if question_group_id == 0 else QuizTypeMultipleChoice
            explanation = self.transform_text(question_dict.get('explanation'))
            links = self._process_links(question_dict.get('question_audio'), question_dict.get('guide_videos'), question_dict.get('question_images'))
            quiz_options = []
            for label_key in ['a', 'b', 'c', 'd']:
                option_content = self.transform_text(question_dict.get(f'label_{label_key}'))
                if question_dict.get(f'correct_answer') == f'label_{label_key}':
                    quiz_options.append(dict(label=label_key, content=option_content, is_correct=True))
                else:
                    quiz_options.append(dict(label=label_key, content=option_content, is_correct=False))
            quiz_answer = ''
            
            question = QuizQuestion(
                quiz_question_group_id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                quiz_type = quiz_type,
                quiz_options = json.dumps(quiz_options),
                explanation = explanation,
                links = json.dumps(links),
                quiz_answer = quiz_answer,
                level = self._process_level(question_dict.get('question_levels')),
            )
            return question, original_question_id, is_existed
    
    def _process_essay(self, question_dict: Dict[str, Any], question_group_id: int):
        original_question_id = question_dict.get('id')
        question, is_existed = self._is_question_existed(original_question_id)
        if is_existed:
            return question, original_question_id, is_existed
        else:
            original_text = self.transform_text(question_dict.get('question_content'))
            parsed_text = original_text
            quiz_type = QuizTypeSingleEssay
            explanation = self.transform_text(question_dict.get('explanation'))
            links = self._process_links(question_dict.get('question_audio'), question_dict.get('guide_videos'), question_dict.get('question_images'))
            quiz_options = ''
            quiz_answer = self.transform_text(question_dict.get('answer'))
            
            question = QuizQuestion(
                quiz_question_group_id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                quiz_type = quiz_type,
                quiz_options = quiz_options,
                explanation = explanation,
                links = json.dumps(links),
                quiz_answer = quiz_answer,
                level = self._process_level(question_dict.get('question_levels')),
            )
            return question, original_question_id, is_existed
    
    def _process_group_quiz(self, group_question_dict):
        flag = True
        question_list = []
        original_question_ids = []
        question_group_id = group_question_dict.get('id')
        
        for question_dict in group_question_dict.get('related_quizzes'):
            question, original_question_id, is_existed = self._process_quiz(question_dict, question_group_id)
            question_list.append(question)
            original_question_ids.append(original_question_id)
            flag = flag and is_existed

        if flag is False:
            original_text = self.transform_text(group_question_dict.get('group_content'))
            parsed_text = original_text
            links = self._process_links(group_question_dict.get('group_audio'), group_question_dict.get('guide_videos'), group_question_dict.get('group_images'))
            question_group = QuizQuestionGroup(
                id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                links = json.dumps(links),
            )
            return question_group, question_list, original_question_ids, flag
        
        return None, question_list, original_question_ids, flag
    
    def _process_group_essay(self, group_question_dict):
        flag = True
        question_list = []
        original_question_ids = []
        question_group_id = group_question_dict.get('id')
        
        for question_dict in group_question_dict.get('related_essays', []):
            question, original_question_id, is_existed = self._process_essay(question_dict, question_group_id)
            question_list.append(question)
            original_question_ids.append(original_question_id)
            flag = flag and is_existed
        
        if flag is False:
            original_text = self.transform_text(group_question_dict.get('group_content'))
            parsed_text = original_text
            links = self._process_links(group_question_dict.get('group_audio'), group_question_dict.get('guide_videos'), group_question_dict.get('group_images'))
            question_group = QuizQuestionGroup(
                id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                links = json.dumps(links),
            )
        
            return question_group, question_list, original_question_ids, flag
        
        return None, question_list, original_question_ids, flag
    
    def _process_single_text_entry(self, question_dict, question_group_id: int):
        original_question_id = question_dict.get('id')
        question, is_existed = self._is_question_existed(original_question_id)
        if is_existed:
            return question, original_question_id, is_existed
        else:
            original_text = self.transform_text(question_dict.get('question_content'))
            parsed_text = original_text
            quiz_type = QuizTypeBlankFilling
            explanation = self.transform_text(question_dict.get('explanation'))
            links = self._process_links(question_dict.get('question_audio'), question_dict.get('guide_videos'), question_dict.get('question_images'))
            quiz_options = ''
            quiz_answer = self.transform_text(question_dict.get('answer'))

            question = QuizQuestion(
                quiz_question_group_id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                quiz_type = quiz_type,
                quiz_options = quiz_options,
                explanation = explanation,
                links = json.dumps(links),
                quiz_answer = quiz_answer,
                level = self._process_level(question_dict.get('question_levels')),
            )
            return question, original_question_id, is_existed
    
    def _process_group_text_entry(self, group_question_dict):
        flag = True
        question_list = []
        original_question_ids = []
        question_group_id = group_question_dict.get('id')
        
        for question_dict in group_question_dict.get('related_questions'):
            question, original_question_id, is_existed = self._process_single_text_entry(question_dict, question_group_id)
            question_list.append(question)
            original_question_ids.append(original_question_id)
            flag = flag and is_existed
        
        if flag is False:
            original_text = self.transform_text(group_question_dict.get('group_content'))
            parsed_text = original_text
            links = self._process_links(group_question_dict.get('group_audio'), group_question_dict.get('guide_videos'), group_question_dict.get('group_images'))
            question_group = QuizQuestionGroup(
                id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                links = json.dumps(links),
            )
            return question_group, question_list, original_question_ids, flag
        
        return None, question_list, original_question_ids, flag
    
    def _process_single_quiz_true_false(self, question_dict, question_group_id: int):
        original_question_id = question_dict.get('id')
        question, is_existed = self._is_question_existed(original_question_id)
        if is_existed:
            return question, original_question_id, is_existed
        else:
            original_text = self.transform_text(question_dict.get('question_content'))
            parsed_text = original_text
            quiz_type = QuizTypeSingleChoice if question_group_id == 0 else QuizTypeMultipleChoice
            explanation = self.transform_text(question_dict.get('explanation'))
            links = self._process_links(question_dict.get('question_audio'), question_dict.get('guide_videos'), question_dict.get('question_images'))
            quiz_answer = question_dict.get('answer', False)
            quiz_options = []
            if quiz_answer is True:
                quiz_options.append(dict(label='a', content='True', is_correct=True))
                quiz_options.append(dict(label='b', content='False', is_correct=False))
            if quiz_answer is False:
                quiz_options.append(dict(label='a', content='True', is_correct=False))
                quiz_options.append(dict(label='b', content='False', is_correct=True))
            
            question = QuizQuestion(
                quiz_question_group_id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                quiz_type = quiz_type,
                quiz_options = json.dumps(quiz_options),
                explanation = explanation,
                links = json.dumps(links),
                quiz_answer = quiz_answer,
                level = self._process_level(question_dict.get('question_levels')),
            )
            return question, original_question_id, is_existed
    
    def _process_group_quiz_true_false(self, group_question_dict):
        flag = True
        question_list = []
        original_question_ids = []
        question_group_id = group_question_dict.get('id')
        
        for question_dict in group_question_dict.get('related_questions'):
            question, original_question_id, is_existed = self._process_single_quiz_true_false(question_dict, question_group_id)
            question_list.append(question)
            original_question_ids.append(original_question_id)
            flag = flag and is_existed
        
        if flag is False:
            original_text = self.transform_text(group_question_dict.get('group_content'))
            parsed_text = original_text
            links = self._process_links(group_question_dict.get('group_audio'), group_question_dict.get('guide_videos'), group_question_dict.get('group_images'))
            question_group = QuizQuestionGroup(
                id = question_group_id,
                original_text = original_text,
                parsed_text = parsed_text,
                links = json.dumps(links),
            )
            return question_group, question_list, original_question_ids, flag
            
        return None, question_list, original_question_ids, flag
    
    def _process_question(self, question_dict):
        
        group_question_list = []
        processed_question_list = []
        uniqid_list = []
        original_question_id_list = []

        question_type = question_dict.get('__component')

        if question_type == 'course.quiz':
            question, original_question_id, is_existed = self._process_quiz(question_dict, 0)
            processed_question_list.append(question)
            if not is_existed:
                uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            original_question_id_list.append(original_question_id)
            
        if question_type == 'course.group-quiz':
            question_group, question_list, original_question_ids, is_existed = self._process_group_quiz(question_dict)
            original_question_id_list.extend(original_question_ids)
            processed_question_list.extend(question_list)
            if not is_existed:
                group_question_list.append(question_group)
                for _ in question_list:
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))

        if question_type == 'course.essay':
            question, original_question_id, is_existed = self._process_essay(question_dict, 0)
            processed_question_list.append(question)
            if not is_existed:
                uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                uniqid_list.append(None)
            original_question_id_list.append(original_question_id)

        if question_type == 'course.group-essay':
            question_group, question_list, original_question_ids, is_existed = self._process_group_essay(question_dict)
            original_question_id_list.extend(original_question_ids)
            processed_question_list.extend(question_list)
            if question_group:
                group_question_list.append(question_group)
                for _ in question_list:
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                for _ in question_list:
                    uniqid_list.append(None)

        if question_type == 'course.single-text-entry':
            question, original_question_id, is_existed = self._process_single_text_entry(question_dict, 0)
            processed_question_list.append(question)
            if not is_existed:
                uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                uniqid_list.append(None)
            original_question_id_list.append(original_question_id)

        if question_type == 'course.group-text-entry':
            question_group, question_list, original_question_ids, is_existed = self._process_group_text_entry(question_dict)
            original_question_id_list.extend(original_question_ids)
            processed_question_list.extend(question_list)
            if question_group:
                group_question_list.append(question_group)
                for _ in question_list:
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                for _ in question_list:
                    uniqid_list.append(None)
            

        if question_type == 'course.single-quiz-true-false':
            question, original_question_id, is_existed = self._process_single_quiz_true_false(question_dict, 0)
            processed_question_list.append(question)
            if not is_existed:
                uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                uniqid_list.append(None)
            original_question_id_list.append(original_question_id)

        if question_type == 'course.group-quiz-true-false':
            question_group, question_list, original_question_ids, is_existed = self._process_group_quiz_true_false(question_dict)
            original_question_id_list.extend(original_question_ids)
            processed_question_list.extend(question_list)
            if question_group:
                group_question_list.append(question_group)
                for _ in question_list:
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
            else:
                for _ in question_list:
                    uniqid_list.append(None)

        return group_question_list, processed_question_list, uniqid_list, original_question_id_list, is_existed



    def _process_collection(self, question_item_list):
        # try:
            id_map_list = []
            new_question_list = []
            logger.info(f"Start importing {len(question_item_list)} questions") 

            for question_dict in question_item_list:
                group_question_list, processed_question_list, uniqid_list, original_question_id_list, is_existed = self._process_question(question_dict)

                if is_existed:
                    for question_idx, question in enumerate(processed_question_list):
                        id_map_list.append({'original_id': original_question_id_list[question_idx],
                                            'new_id': question.id,
                                            'level': question.level})
                else:
                    self.session.add_all(uniqid_list)
                    self.session.commit()

                    group_question_id = None
                    if group_question_list:
                        group_question_list[0].id = None # with 1 question, we only have 1 group question
                        self.session.add(group_question_list[0])
                        self.session.commit()
                        group_question_id = group_question_list[0].id

                    for question_idx, question in enumerate(processed_question_list):
                        if question is None:
                            print(original_question_id_list)
                            print(processed_question_list)
                        question.id = uniqid_list[question_idx].to_uniqid_number()
                        if group_question_id:
                            question.quiz_question_group_id = group_question_id
                        new_question_list.append(question)

                        id_map_list.append({'original_id': original_question_id_list[question_idx],
                                            'new_id': question.id,
                                            'level': question.level})
                
            if new_question_list:
                self.session.add_all(new_question_list)
                self.session.commit()

            logger.info(f"Imported {len(processed_question_list)} questions")
            return id_map_list
        
        # except Exception as e:
        #     logger.error(f"Error processing questions: {e}")
        #     return []
        
    def _create_collection(self, id_map_list, level, grade_id, subject_id):
        collection_name = {0: 'Cấp độ ngẫu nhiên', 1: 'Cấp độ nhận biết', 2: 'Cấp độ thông hiểu', 3: 'Cấp độ vận dụng', 4: 'Cấp độ vận dụng cao'}.get(level)
        try:   
            if id_map_list:
                collection = QuizCollectionGroup(
                    id = self._get_uniqid(ObjectTypeStrMapping[QuizCollectionGroupType]),
                    name = collection_name,
                    grade_id=grade_id,
                    subject_id=subject_id,
                    quiz_count=len(id_map_list),
                )
                self.session.add(collection)
                self.session.flush()

                quiz_collection_list = []
                question_id_list = []

                for id_map in id_map_list:
                    question_id = id_map.get('new_id')
                    original_question_id = id_map.get('original_id')
                    question_id_list.append([original_question_id, question_id])
                    quiz_collection_list.append(QuizCollection(
                        id = self._get_uniqid(ObjectTypeStrMapping[QuizCollectionType]),
                        quiz_id = question_id,
                        quiz_collection_group_id = collection.id
                    ))
                self.session.add_all(quiz_collection_list)
                self.session.commit()

                logger.info(f"Created `{collection_name}` collection for {len(id_map_list)} questions")
                collection_item = [collection, question_id_list]
                return collection_item
        except Exception as e:
            logger.error(f"Error creating `{collection_name}` collection: {e}")
            return []

        
    def process_practices(self, question_item_list, grade_id, subject_id):
        try:
            nonlevel_question_list = []
            nb_level_question_list = []
            th_level_question_list = []
            vd_level_question_list = []
            vdc_level_question_list = []


            logger.info(f"Start processing collections for {len(question_item_list)} questions")

            id_map_list = self._process_collection(question_item_list)
            for id_map in id_map_list:
                level = id_map.get('level')
                if level == 0:
                    nonlevel_question_list.append(id_map)
                elif level == 1:
                    nb_level_question_list.append(id_map)
                elif level == 2:
                    th_level_question_list.append(id_map)
                elif level == 3:
                    vd_level_question_list.append(id_map)
                elif level == 4:
                    vdc_level_question_list.append(id_map)

            collection_list = []
            collection_list.append(self._create_collection(nonlevel_question_list, 0, grade_id, subject_id))
            collection_list.append(self._create_collection(nb_level_question_list, 1, grade_id, subject_id))
            collection_list.append(self._create_collection(th_level_question_list, 2, grade_id, subject_id))
            collection_list.append(self._create_collection(vd_level_question_list, 3, grade_id, subject_id))
            collection_list.append(self._create_collection(vdc_level_question_list, 4, grade_id, subject_id))


            collection_list = list(filter(None, collection_list))

            logger.info(f"Imported {len(collection_list)} collections")
            return collection_list

        except Exception as e:
            logger.error(f"Error processing collections: {e}")
            return []

    def process_theory_examples(self, theory_id: int, course_lecture_id: int, question_item_list: List[Dict[str, Any]]) -> List[CourseIDMapping]:
        try:
            logger.info(f"Start processing theory examples for theory {theory_id}: {len(question_item_list)} questions")
            # original_question_id_list, processed_question_id_list = self._process_collection(question_item_list)
            id_map_list = self._process_collection(question_item_list)
            theory_example_list = []
            question_id_mapping_list = []
            for current_position, id_map in enumerate(id_map_list):
                theory_example_list.append(TheoryExample(
                    theory_id = theory_id,
                    question_id = id_map.get('new_id'),
                    position = current_position
                ))
                question_id_mapping_list.append(self.create_course_id_mapping(id_map.get('original_id'), id_map.get('new_id'), 'question', course_lecture_id, 'insert'))

            self.session.add_all(theory_example_list)
            self.session.commit()
            logger.info(f"Processed {len(question_item_list)} theory examples for theory {theory_id}")
            return question_id_mapping_list
        except Exception as e:
            logger.error(f"Error processing theory examples: {e}")
            return []
 
    def process_media(self, media_data: Dict[str, Any]) -> Media:
        try:
            media = Media(
                id = self._get_uniqid(ObjectTypeStrMapping[MediaType]),
                name = media_data.get('name'),
                url = media_data.get('url'),
                title = media_data.get('title'),
                caption = media_data.get('caption'),
                mine_type = media_data.get('mine_type'),
            )
            # self.session.add(media)
            # self.session.flush()
            logger.info(f"Processed media {media.id}")
            return media
        except Exception as e:
            logger.error(f"Error processing media: {e}")
            return None

    def create_course_id_mapping(self, original_id: int, new_id: int, entity_type: str, parent_new_id: int, task_name: str) -> CourseIDMapping:
        course_id_mapping = CourseIDMapping(
            original_id = original_id,
            new_id = new_id,
            entity_type = entity_type,
            parent_new_id = parent_new_id,
            task_name = task_name
        )
        logger.info(f"ID mapping for {task_name}: {parent_new_id} {entity_type}: {original_id} -> {new_id}")

        return course_id_mapping
    


    def process_paper_exam_collection(self, paper_exam_collection_list, grade_id, subject_id):
        paper_exam_collection_group_list = []
        paper_exam_collections_list = []
        for paper_exam_collection_data in paper_exam_collection_list:
            des_exam_id_list = []
            paper_exam_collections = self.get_data_dict(id=paper_exam_collection_data.get('id'), type='paper_exam_collection')
            for paper_exam in paper_exam_collections.get('paperExams'):
                exam_id = paper_exam.get('id')
                imported_des_exam_id = self.exam_importer.import_exam(exam_id)
                if imported_des_exam_id:
                    des_exam_id_list.append(imported_des_exam_id)

            paper_exam_collection_group = QuizCollectionGroup(
                id = self._get_uniqid(ObjectTypeStrMapping[QuizCollectionGroupType]),
                name = paper_exam_collection_data.get('title'),
                grade_id=grade_id,
                subject_id=subject_id,
                quiz_count=len(des_exam_id_list),
            )
            self.session.add(paper_exam_collection_group)
            self.session.flush()

            quiz_collection_list = []
            for des_exam_id in des_exam_id_list:
                paper_exam_collection = QuizCollection(
                    id = self._get_uniqid(ObjectTypeStrMapping[QuizCollectionType]),
                    quiz_id = des_exam_id,
                    quiz_collection_group_id = paper_exam_collection_group.id
                )
                quiz_collection_list.append(paper_exam_collection)
            self.session.add_all(quiz_collection_list)
            self.session.commit()
            paper_exam_collection_group_list.append(paper_exam_collection_group)
            paper_exam_collections_list.append(paper_exam_collections)

        return paper_exam_collection_group_list, paper_exam_collections_list





    