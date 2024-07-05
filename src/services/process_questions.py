import json
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from src.models.exam_bank_models_for_course import Uniqid, QuizCollection, QuizCollectionGroup, QuizQuestion, QuizQuestionGroup, TheoryExample
from src.commons import ObjectTypeStrMapping, QuizTypeSingleChoice, QuizTypeMultipleChoice, QuizTypeSingleEssay, QuizCollectionGroupType, \
    QuizCollectionType, QuizQuestionType
from src.services.logger_config import setup_logger

logger = setup_logger()


class QuestionProcessor:
    def __init__(self, session: Session, theory_example: bool, theory_id: int, current_position: int,question_list: List[Dict[str, Any]], question_type: str, quiz_collection_name: str,
                 user_id: int, grade_id: int, subject_id: int,):
        self.session = session
        self.theory_example = theory_example
        self.theory_id = theory_id
        self.current_position = current_position
        self.question_list = question_list
        self.question_type = question_type.lower()
        self.quiz_collection_name = quiz_collection_name
        self.user_id = user_id
        self.grade_id = grade_id
        self.subject_id = subject_id
    
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

    def process_level(self, level: list):
        if not level:
            return 0
        level_id = level[0].get('id')
        if level_id == 6:
            return 1
        if level_id == 7:
            return 2
        if level_id == 8:
            return 3
        if level_id == 9:
            return 4

    def get_uniqid(self, uniqid_type):
        uniqid = Uniqid(uniqid_type=uniqid_type)
        self.session.add(uniqid)
        self.session.flush()
        uniqid = uniqid.to_uniqid_number()
        return uniqid

    def process_questions_old_version(self):
        try:

            question_uniqid_list = []
            quiz_collection_uniqid_list = []
            processed_question_list = []

            if self.question_type == 'quiz':
                quiz_type = QuizTypeSingleChoice
            if self.question_type == 'essay':
                quiz_type = QuizTypeSingleEssay
            for question_idx, question_dict in enumerate(self.question_list[:3]):

                quiz_options = []
                for label_key in ['a', 'b', 'c', 'd']:
                    option_content = self.transform_data(question_dict.get(f'label_{label_key}'))
                    if question_dict.get('correct_answer') == f'label_{label_key}':
                        quiz_options.append(dict(label=label_key, content=option_content, is_correct=True))
                    else:
                        quiz_options.append(dict(label=label_key, content=option_content, is_correct=False))
                
                links = {"audio_links": [], "video_links": [], "image_links": []}
                question_audio = question_dict.get('question_audio', None)
                if question_audio:
                    question_audio = question_audio.get('url', '')
                    links["audio_links"].append(question_audio)
                question_images = question_dict.get('question_images', None)
                if question_images:
                    question_images = question_images.get('url', '')
                    links["image_links"].append(question_images)

                question = QuizQuestion(
                    quiz_question_group_id=0,
                    original_text=self.transform_data(question_dict.get('question_content', '')),
                    parsed_text=self.transform_data(question_dict.get('question_content', '')),
                    quiz_type=quiz_type,
                    quiz_options=json.dumps(quiz_options) if quiz_options else '',
                    explanation=self.transform_data(question_dict.get('explanation', '')),
                    links=json.dumps(links),
                    quiz_answer=question_dict.get('answer', ''),
                    level=self.process_level(question_dict.get('level', [])),
                )

                processed_question_list.append(question)
                question_uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                if not self.theory_example:
                    quiz_collection_uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))

            self.session.add_all(question_uniqid_list)
            self.session.flush()
            if not self.theory_example:
                self.session.add_all(quiz_collection_uniqid_list)

                quiz_collection_group = QuizCollectionGroup(
                    name=self.quiz_collection_name,
                    # user_id=self.user_id,
                    grade_id=self.grade_id,
                    subject_id=self.subject_id,
                    quiz_count=len(processed_question_list),
                )

                quiz_collection_group_uniqid = self.get_uniqid(ObjectTypeStrMapping[QuizCollectionGroupType])
                quiz_collection_group.id = quiz_collection_group_uniqid
                self.session.add(quiz_collection_group)
                self.session.flush()

                quiz_collection_list = []

                for question_idx, question in enumerate(processed_question_list):
                    question.id = question_uniqid_list[question_idx].to_uniqid_number()
                    quiz_collection_list.append(QuizCollection(
                        id=quiz_collection_uniqid_list[question_idx].to_uniqid_number(),
                        quiz_id=question.id,
                        quiz_collection_group_id=quiz_collection_group.id,
                    ))
                self.session.add_all(processed_question_list)
                self.session.add_all(quiz_collection_list)
                self.session.commit()
                logger.info(f"Processed {len(processed_question_list)} questions for quiz_collection_group_id: {quiz_collection_group.id}")
                return quiz_collection_group.id, self.current_position
            else:
                theory_example_list = []

                for question_idx, question in enumerate(processed_question_list):
                    question.id = question_uniqid_list[question_idx].to_uniqid_number()
                    theory_example_list.append(TheoryExample(
                        # id=question.id,
                        theory_id=self.theory_id,
                        question_id=question.id,
                        position=self.current_position,
                    ))
                    self.current_position += 1
                self.session.add_all(processed_question_list)
                self.session.add_all(theory_example_list)
                self.session.commit()
                logger.info(f"Processed {len(processed_question_list)} questions for theory_id: {self.theory_id}")
                return self.theory_id, self.current_position
        except Exception as e:
            logger.error(f"Error: {e}")
            return None, 0
        

