import json
from typing import Any, Dict, List, Optional, Tuple
from src.commons import ObjectTypeStrMapping, ExamType, QuizTypeSingleChoice, QuizTypeSingleEssay, QuizTypeSingleChoiceFromQuiz,\
    QuizTypeMultipleChoice, QuizTypeBlankFilling, QuizQuestionType, GradeIDMapping, SubjectIDMapping
from src.models.exam_bank_models import Exam, Uniqid, QuizQuestion, QuizQuestionGroup, ExamQuestion, TrackingLogs, Base
from src.config.config import settings
from sqlalchemy.orm import Session
import requests
import asyncio
import re
from src.services.logger import log_runtime


class PrepExamData:
    def __init__(self,
                 exam: Exam,
                 quiz_question_group_list: List[QuizQuestionGroup],
                 quiz_question_list: List[QuizQuestion],
                 uniqid_list: List[Uniqid],
                 quiz_info_list: List,):
        self.exam = exam
        self.quiz_question_group_list = quiz_question_group_list
        self.quiz_question_list = quiz_question_list
        self.uniqid_list = uniqid_list
        self.quiz_info_list = quiz_info_list


class ExamParser:
    def __init__(self, session_import: Session, session_log: Session):
        self.session_import = session_import
        self.session_log = session_log
        
    # @log_runtime    
    def extract_data(self, exam_id):
        auth_token = settings.api_authentication_token
        url = settings.api_get_by_exam_id.format(EXAM_ID=exam_id)
        headers = {
            'Authorization': f'Bearer {auth_token}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data')
        return dict()
    

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
    
    # @log_runtime
    def parse_as_dict_collections(self, exam_id) -> Optional[PrepExamData]:
        exam_data = self.extract_data(exam_id=exam_id)
        
        if exam_data:
            exam = Exam(
                title=exam_data.get('title'),
                term=exam_data.get('examTerm'),
                duration=exam_data.get('duration'),
                school_year=exam_data.get('schoolYear'),
                description="",
                subject_id=0 if exam_data.get('subject') is None else self.mapping_id(SubjectIDMapping, exam_data.get('subject').get('id')),
                grade_id=0 if exam_data.get('grade') is None else self.mapping_id(GradeIDMapping, exam_data.get('grade').get('id')),
                # subject_id = 11,
                # grade_id = 6,
                school_id=0 if exam_data.get('school') is None else exam_data.get('school').get('id'),
                subdivision_id=0,
                checkpoints=0,
                updated_at=exam_data.get('updatedAt'),
            )
            src_exam_id = exam_data.get('id')
            quiz_info_list = []
            quiz_question_list = []
            quiz_question_group_list = []
            uniqid_list = []
            uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[ExamType]))
            for item in exam_data.get('relatedItems'):
                component_type = item.get('__component')

                if component_type == 'exam.single-quiz-from-quiz':
                    quiz_question, quiz_info_dict = self.parse_single_quiz_question_from_quiz(item, src_exam_id)
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                    quiz_question_list.append(quiz_question)
                    quiz_info_list.append(quiz_info_dict)

                if component_type == 'exam.single-quiz':
                    quiz_question, quiz_info_dict = self.parse_single_quiz_question(item, src_exam_id)
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                    quiz_question_list.append(quiz_question)
                    quiz_info_list.append(quiz_info_dict)
                
                if component_type == 'exam.grouped-quiz':
                    group_quiz_question, quiz_questions, group_quiz_info_list = self.parse_multiple_quiz_question(item, src_exam_id)
                    for _ in quiz_questions:
                        uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                    quiz_question_list.extend(quiz_questions)
                    quiz_question_group_list.append(group_quiz_question)
                    quiz_info_list.extend(group_quiz_info_list)

                if component_type == 'exam.single-essay':
                    quiz_question, quiz_info_dict = self.parse_single_essay_question(item, src_exam_id)
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                    quiz_question_list.append(quiz_question)
                    quiz_info_list.append(quiz_info_dict)

                if component_type == 'exam.grouped-essay':
                    group_quiz_question, quiz_questions, group_quiz_info_list = self.parse_multiple_essay_question(item, src_exam_id)
                    for _ in quiz_questions:
                        uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))

                    quiz_question_list.extend(quiz_questions)
                    quiz_question_group_list.append(group_quiz_question)
                    quiz_info_list.extend(group_quiz_info_list)

                if component_type == 'exam.single-text-entry':
                    quiz_question, quiz_info_dict = self.parse_single_text_entry_question(item, src_exam_id)
                    uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))
                    quiz_question_list.append(quiz_question)
                    quiz_info_list.append(quiz_info_dict)

                if component_type == 'exam.group-entry-text':
                    group_quiz_question, quiz_questions, group_quiz_info_list = self.parse_multiple_text_entry_question(item, src_exam_id)
                    for _ in quiz_questions:
                        uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))

                    quiz_question_list.extend(quiz_questions)
                    quiz_question_group_list.append(group_quiz_question)
                    quiz_info_list.extend(group_quiz_info_list)
                #     pass

                if component_type == 'exam.group-quiz-true-false':
                    group_quiz_question, quiz_questions, group_quiz_info_list = self.parse_multiple_true_false_question(item, src_exam_id)
                    for _ in quiz_questions:
                        uniqid_list.append(Uniqid(uniqid_type=ObjectTypeStrMapping[QuizQuestionType]))

                    quiz_question_list.extend(quiz_questions)
                    quiz_question_group_list.append(group_quiz_question)
                    quiz_info_list.extend(group_quiz_info_list)

            return PrepExamData(exam, quiz_question_group_list, quiz_question_list, uniqid_list, quiz_info_list)
        return None
    
    # @log_runtime
    def mapping_id(self, mapping_dict, id):
        mapped_id = mapping_dict.get(id)
        if mapped_id:
            return mapped_id
        else:
            return 0

    # @log_runtime
    def parse_single_quiz_question_from_quiz(self, item: Dict[str, Any], exam_id: int , quiz_question_group_id: int = 0) -> Tuple[QuizQuestion, Dict[str, Any]]:
        original_text = self.transform_data(item.get('questionContent') if item.get('questionContent') is not None else "")
        parsed_text = original_text
        quiz_type = QuizTypeMultipleChoice if quiz_question_group_id else QuizTypeSingleChoiceFromQuiz
        explanation = self.transform_data(item.get('longAnswer') if item.get('longAnswer') is not None else "")
        links = {"audio_links": [], "video_links": [], "image_links": []}
        question_audio = item.get('questionAudio')
        if question_audio:
            links["audio_links"].append(question_audio)
        question_images = item.get('questionImages')
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))
        quiz_options = []
        for label_key in ['A', 'B', 'C', 'D']:
            option_content = self.transform_data(item.get(f'label{label_key}'))
            if item.get('correctLabel') == f'label{label_key}':
                quiz_options.append(dict(label=label_key, content=option_content, is_correct=True))
            else:
                quiz_options.append(dict(label=label_key, content=option_content, is_correct=False))
        quiz_answer = item.get('answer', '')
        return QuizQuestion(
            original_text=original_text,
            parsed_text=parsed_text,
            quiz_type=quiz_type,
            quiz_options=json.dumps(quiz_options),
            quiz_question_group_id=quiz_question_group_id,
            explanation=explanation or '',
            links=json.dumps(links),
            quiz_answer=quiz_answer
        ), {
            "src_exam_id": exam_id,
            "src_quiz_object_type": quiz_type,
            "src_quiz_question_id": item.get('id'),
            "src_quiz_question_group_id": quiz_question_group_id,
        }
    # @log_runtime
    def parse_single_quiz_question(self, item: Dict[str, Any], exam_id: int , quiz_question_group_id: int = 0) -> Tuple[QuizQuestion, Dict[str, Any]]:
        original_text = self.transform_data(item.get('questionContent') if item.get('questionContent') is not None else "")
        parsed_text = original_text
        quiz_type = QuizTypeMultipleChoice if quiz_question_group_id else QuizTypeSingleChoice
        explanation = self.transform_data(item.get('longAnswer') if item.get('longAnswer') is not None else "")
        links = {"audio_links": [], "video_links": [], "image_links": []}
        question_audio = item.get('questionAudio')
        if question_audio:
            links["audio_links"].append(question_audio)
        question_images = item.get('questionImages')
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))
        quiz_options = []
        for label_key in ['A', 'B', 'C', 'D']:
            option_content = self.transform_data(item.get(f'label{label_key}'))
            if item.get('correctLabel') == f'label{label_key}':
                quiz_options.append(dict(label=label_key, content=option_content, is_correct=True))
            else:
                quiz_options.append(dict(label=label_key, content=option_content, is_correct=False))
        quiz_answer = item.get('answer', '')
        return QuizQuestion(
            original_text=original_text,
            parsed_text=parsed_text,
            quiz_type=quiz_type,
            quiz_options=json.dumps(quiz_options),
            quiz_question_group_id=quiz_question_group_id,
            explanation=explanation or '',
            links=json.dumps(links),
            quiz_answer=quiz_answer
        ), {
            "src_exam_id": exam_id,
            "src_quiz_object_type": quiz_type,
            "src_quiz_question_id": item.get('id'),
            "src_quiz_question_group_id": quiz_question_group_id,
        }
    # @log_runtime
    def parse_multiple_quiz_question(self, group_item: Dict[str, Any], exam_id: int) -> Tuple[QuizQuestionGroup, List[QuizQuestion]]:
        quiz_questions = []
        group_quiz_info_list = []
        quiz_question_group_id = group_item.get('id')
        group_original_text = self.transform_data(group_item.get('groupContent') if group_item.get('groupContent') is not None else "")
        group_parsed_text = group_original_text

        group_links = {"audio_links": [], "video_links": [], "image_links": []}
        group_question_audio = group_links.get('groupAudio')
        if group_question_audio:
            group_links["audio_links"].append(group_question_audio)

        group_images = group_item.get('groupImages')
        if group_images:
            for image in group_images:
                group_links["image_links"].append(image.get('url'))
        question_group = QuizQuestionGroup(
            id=quiz_question_group_id,
            original_text=group_original_text or '',
            parsed_text=group_parsed_text or '',
            links=json.dumps(group_links),
        )

        for item in group_item.get('relatedQuizzes', []):
            quiz_question, quiz_info_dict = self.parse_single_quiz_question(item, exam_id, quiz_question_group_id)
            quiz_questions.append(quiz_question)
            group_quiz_info_list.append(quiz_info_dict)

        return question_group, quiz_questions, group_quiz_info_list

    # @log_runtime
    def parse_single_essay_question(self, item: Dict[str, Any], exam_id: int , quiz_question_group_id: int = 0) -> Tuple[QuizQuestion, Dict[str, Any]]:
        original_text = self.transform_data(item.get('questionContent') if item.get('questionContent') is not None else "")
        parsed_text = original_text
        # quiz_type = QuizTypeGroupEssay if quiz_question_group_id else QuizTypeSingleEssay
        quiz_type = QuizTypeSingleEssay
        explanation = self.transform_data(item.get('longAnswer') if item.get('longAnswer') is not None else "")
        links = {"audio_links": [], "video_links": [], "image_links": []}
        question_audio = item.get('questionAudio')
        if question_audio:
            links["audio_links"].append(question_audio)
        question_images = item.get('questionImages')
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))
        quiz_answer = item.get('answer', '')
        return QuizQuestion(
            original_text=original_text,
            parsed_text=parsed_text,
            quiz_type=quiz_type,
            quiz_options='',
            quiz_question_group_id=quiz_question_group_id,
            explanation=explanation or '',
            links=json.dumps(links),
            quiz_answer=quiz_answer
        ), {
            "src_exam_id": exam_id,
            "src_quiz_object_type": quiz_type,
            "src_quiz_question_id": item.get('id'),
            "src_quiz_question_group_id": quiz_question_group_id,
        }
    
    # @log_runtime
    def parse_multiple_essay_question(self, group_item: Dict[str, Any], exam_id: int) -> Tuple[QuizQuestionGroup, List[QuizQuestion]]:
        quiz_questions = []
        group_quiz_info_list = []
        quiz_question_group_id = group_item.get('id')
        group_original_text = self.transform_data(group_item.get('groupContent') if group_item.get('groupContent') is not None else "")
        group_parsed_text = group_original_text

        group_links = {"audio_links": [], "video_links": [], "image_links": []}
        group_question_audio = group_links.get('groupAudio')
        if group_question_audio:
            group_links["audio_links"].append(group_question_audio)

        group_images = group_item.get('groupImages')
        if group_images:
            for image in group_images:
                group_links["image_links"].append(image.get('url'))
        question_group = QuizQuestionGroup(
            id=quiz_question_group_id,
            original_text=group_original_text or '',
            parsed_text=group_parsed_text or '',
            links=json.dumps(group_links),
        )

        for item in group_item.get('relatedEssays', []):
            quiz_question, quiz_info_dict = self.parse_single_essay_question(item, exam_id, quiz_question_group_id)
            quiz_questions.append(quiz_question)
            group_quiz_info_list.append(quiz_info_dict)

        return question_group, quiz_questions, group_quiz_info_list

    # @log_runtime
    def parse_single_text_entry_question(self, item: Dict[str, Any], exam_id: int, quiz_question_group_id: int = 0) -> Tuple[QuizQuestion, Dict[str, Any]]:
        original_text = self.transform_data(item.get('questionContent') if item.get('questionContent') is not None else "")
        parsed_text = original_text
        quiz_type = QuizTypeBlankFilling
        explanation = item.get('longAnswer') if item.get('longAnswer') is not None else ""
        links = {"audio_links": [], "video_links": [], "image_links": []}
        question_audio = item.get('questionAudio')
        if question_audio:
            links["audio_links"].append(question_audio)
        question_images = item.get('questionImages')
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))
        quiz_answer = item.get('answer', '')

        return QuizQuestion(
            original_text=original_text,
            parsed_text=parsed_text,
            quiz_type=quiz_type,
            quiz_options='',
            quiz_question_group_id=quiz_question_group_id,
            explanation=explanation or '',
            links=json.dumps(links),
            quiz_answer=quiz_answer,
        ),{
            "src_exam_id": exam_id,
            "src_quiz_object_type": quiz_type,
            "src_quiz_question_id": item.get('id'),
            "src_quiz_question_group_id": quiz_question_group_id,
        }

    # @log_runtime
    def parse_multiple_text_entry_question(self, group_item: Dict[str, Any], exam_id: int) -> Tuple[QuizQuestionGroup, List[QuizQuestion]]:
        quiz_questions = []
        group_quiz_info_list = []
        quiz_question_group_id = group_item.get('id')
        group_original_text = self.transform_data(group_item.get('groupContent') if group_item.get('groupContent') is not None else "")
        group_parsed_text = group_original_text

        group_links = {"audio_links": [], "video_links": [], "image_links": []}
        group_question_audio = group_links.get('groupAudio')
        if group_question_audio:
            group_links["audio_links"].append(group_question_audio)

        group_images = group_item.get('groupImages')
        if group_images:
            for image in group_images:
                group_links["image_links"].append(image.get('url'))
        question_group = QuizQuestionGroup(
            id=quiz_question_group_id,
            original_text=group_original_text or '',
            parsed_text=group_parsed_text or '',
            links=json.dumps(group_links),
        )

        for item in group_item.get('relatedEntries', []):
            quiz_question, quiz_info_dict = self.parse_single_text_entry_question(item, exam_id, quiz_question_group_id)
            quiz_questions.append(quiz_question)
            group_quiz_info_list.append(quiz_info_dict)

        return question_group, quiz_questions, group_quiz_info_list
    
    # @log_runtime
    def parse_single_true_false_question(self, item: Dict[str, Any], exam_id: int , quiz_question_group_id: int = 0) -> Tuple[QuizQuestion, Dict[str, Any]]:
        original_text = self.transform_data(item.get('questionContent') if item.get('questionContent') is not None else "")
        parsed_text = original_text
        quiz_type = QuizTypeMultipleChoice if quiz_question_group_id else QuizTypeSingleChoice
        explanation = item.get('longAnswer') if item.get('longAnswer') is not None else ""
        links = {"audio_links": [], "video_links": [], "image_links": []}
        question_audio = item.get('questionAudio')
        if question_audio:
            links["audio_links"].append(question_audio)
        question_images = item.get('questionImages')
        if question_images:
            for image in question_images:
                links["image_links"].append(image.get('url'))
        quiz_options = []
        quiz_answer = item.get('answer')
        if quiz_answer is True:
            quiz_options.append(dict(label='A', content='True', is_correct=True))
            quiz_options.append(dict(label='B', content='False', is_correct=False))
        if quiz_answer is False:
            quiz_options.append(dict(label='A', content='True', is_correct=False))
            quiz_options.append(dict(label='B', content='False', is_correct=True))

        return QuizQuestion(
            original_text=original_text,
            parsed_text=parsed_text,
            quiz_type=quiz_type,
            quiz_options=json.dumps(quiz_options),
            quiz_question_group_id=quiz_question_group_id,
            explanation=explanation or '',
            links=json.dumps(links),
            quiz_answer=''
        ), {
            "src_exam_id": exam_id,
            "src_quiz_object_type": quiz_type,
            "src_quiz_question_id": item.get('id'),
            "src_quiz_question_group_id": quiz_question_group_id,
        }
    
    # @log_runtime
    def parse_multiple_true_false_question(self, group_item: Dict[str, Any], exam_id: int) -> Tuple[QuizQuestionGroup, List[QuizQuestion]]:
        quiz_questions = []
        group_quiz_info_list = []
        quiz_question_group_id = group_item.get('id')
        group_original_text = self.transform_data(group_item.get('groupContent') if group_item.get('groupContent') is not None else "")
        group_parsed_text = group_original_text

        group_links = {"audio_links": [], "video_links": [], "image_links": []}
        group_question_audio = group_links.get('groupAudio')
        if group_question_audio:
            group_links["audio_links"].append(group_question_audio)

        group_images = group_item.get('groupImages')
        if group_images:
            for image in group_images:
                group_links["image_links"].append(image.get('url'))
        question_group = QuizQuestionGroup(
            id=quiz_question_group_id,
            original_text=group_original_text or '',
            parsed_text=group_parsed_text or '',
            links=json.dumps(group_links),
        )

        for item in group_item.get('relatedQuizzes', []):
            quiz_question, quiz_info_dict = self.parse_single_true_false_question(item, exam_id, quiz_question_group_id)
            quiz_questions.append(quiz_question)
            group_quiz_info_list.append(quiz_info_dict)

        return question_group, quiz_questions, group_quiz_info_list

    # @log_runtime
    def import_exam(self, exam_id: int) -> int:
        exam_data = self.parse_as_dict_collections(exam_id)
        if exam_data:
            quiz_info_list = exam_data.quiz_info_list
            quiz_info_idx = 0
            logs_list = []
            uniqid_idx = 0

            # Register all related ids for the current exam
            uniqid_list = exam_data.uniqid_list
            self.session_import.add_all(uniqid_list)
            self.session_import.commit()

            # Specify exam id and store it
            exam = exam_data.exam
            exam.id = uniqid_list[uniqid_idx].to_uniqid_number()
            exam.num_quizzes = len(exam_data.quiz_question_list)
            uniqid_idx += 1
            self.session_import.add(exam)
            self.session_import.commit()

            # Store all quiz_question_group_list
            ref_quiz_groups = dict()
            quiz_question_group_list = exam_data.quiz_question_group_list
            for group in quiz_question_group_list:
                group_id = group.id
                group.id = None
                self.session_import.add(group)
                self.session_import.commit()
                ref_quiz_groups[group_id] = group.id
            

            # Specify related quizzes and store them
            quiz_question_list = exam_data.quiz_question_list
            for idx, quiz in enumerate(quiz_question_list):
                quiz.id = uniqid_list[uniqid_idx].to_uniqid_number()
                # print(quiz.id)
                uniqid_idx += 1
                ref_group_id = quiz.quiz_question_group_id
                if ref_group_id:
                    quiz.quiz_question_group_id = ref_quiz_groups[ref_group_id]
                quiz_info_dict = quiz_info_list[quiz_info_idx]
                quiz_info_idx += 1
                logs_list.append(TrackingLogs(    
                    src_exam_id = quiz_info_dict.get('src_exam_id'),
                    src_quiz_object_type = quiz_info_dict.get('src_quiz_object_type'),
                    src_quiz_question_id = quiz_info_dict.get('src_quiz_question_id'),
                    src_quiz_question_group_id = quiz_info_dict.get('src_quiz_question_group_id'),
                    des_exam_id = exam.id,
                    des_quiz_question_id = quiz.id,
                    des_quiz_question_group_id = quiz.quiz_question_group_id,
                    task_name = 'insert', # "insert", "update" or "delete"
                    order = idx,
                ))
            self.session_import.add_all(quiz_question_list)
            self.session_import.commit()
            self.session_log.add_all(logs_list)
            self.session_log.commit()

            exam_question_list = []
            for idx, question in enumerate(quiz_question_list):
                exam_question = ExamQuestion(exam_id=exam.id, quiz_question_id=question.id, order=idx, is_checkpoint=False)
                exam_question_list.append(exam_question)

            self.session_import.add_all(exam_question_list)
            self.session_import.commit()
            return exam.id
        return 0
    
# @log_runtime    
def import_exam_bank(session_import: Session, session_log: Session, exam_id: int):
    exam_parser = ExamParser(session_import, session_log)
    exam_id = exam_parser.import_exam(exam_id)
    return exam_id