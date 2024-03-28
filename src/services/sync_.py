import json
from typing import Any, Dict, List, Optional, Tuple
from src.commons import (
    ObjectTypeStrMapping,
    ExamType,
    QuizTypeSingleChoice,
    QuizTypeSingleEssay,
    QuizTypeMultipleChoice,
    QuizTypeBlankFilling,
    QuizQuestionType,
    GradeIDMapping,
    SubjectIDMapping,
)
from src.models.exam_bank_models import (
    Exam,
    Uniqid,
    QuizQuestion,
    QuizQuestionGroup,
    ExamQuestion,
    TrackingLogs,
    Base,
)
from sqlalchemy import and_, asc
from sqlalchemy.orm import Session
import requests
from src.services.import_ import ExamParser
from src.config.config import settings
from src.services.logger import log_runtime, start_info, end_info
import time
import logging
logging.basicConfig(level=logging.INFO, filename="logs/import.log")

class ExamUpdater(ExamParser):
    def __init__(self, session_import: Session, session_log: Session,):
        super().__init__(session_import, session_log)
    @log_runtime
    def extract_data(self, exam_id):
        auth_token = settings.api_authentication_token
        url = settings.api_get_by_exam_id.format(EXAM_ID=exam_id)
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
        return dict()
    @log_runtime
    def get_destination_info(
        self, src_exam_id: int
    ) -> Tuple[int, List[int], Dict[int, int]]:
        result = (
            self.session_log.query(
                TrackingLogs.src_exam_id,
                TrackingLogs.src_quiz_object_type,
                TrackingLogs.src_quiz_question_id,
                TrackingLogs.src_quiz_question_group_id,
                TrackingLogs.des_exam_id,
                TrackingLogs.des_quiz_question_id,
                TrackingLogs.des_quiz_question_group_id,
                TrackingLogs.src_quiz_question_group_id,
            )
            .filter(
                and_(
                    TrackingLogs.src_exam_id == src_exam_id,
                    TrackingLogs.task_name == "insert",
                )
            )
            .order_by(asc(TrackingLogs.des_quiz_question_id))
        )

        des_exam_id = None
        quiz_question_group_id_mapping = {}
        id_mapping = {}
        for r in result:
            (
                src_exam_id,
                src_quiz_object_type,
                src_quiz_question_id,
                src_quiz_question_group_id,
                des_exam_id,
                des_quiz_question_id,
                des_quiz_question_group_id,
                src_quiz_question_group_id,
            ) = r
            if des_quiz_question_group_id != 0:
                quiz_question_group_id_mapping[src_quiz_question_group_id] = (
                    des_quiz_question_group_id
                )
            id_mapping[des_quiz_question_id] = {
                'src_exam_id': src_exam_id, 
                'src_quiz_object_type': src_quiz_object_type, 
                'src_quiz_question_id': src_quiz_question_id, 
                'src_quiz_question_group_id': src_quiz_question_group_id,
            }
            

        return des_exam_id, id_mapping, quiz_question_group_id_mapping
    
    def get_index_by_value(self, data_list, value_dict):
        # Make sure `inner_dict` are unique
        for index, item in enumerate(data_list):
            if item == value_dict:
                return index, item
        return None, dict()
    @log_runtime
    def update_exam(self, src_exam_id):
        des_exam_id, id_mapping, quiz_question_group_id_mapping = self.get_destination_info(src_exam_id)
        exam_data_update = self.parse_as_dict_collections(src_exam_id)
        if exam_data_update:
            # Update exam
            # record_exam = self.session_import.query(Exam).filter(Exam.id == des_exam_id).first()
            # record_exam.title = exam_data_update.exam.title
            # record_exam.term = exam_data_update.exam.term
            # record_exam.description = exam_data_update.exam.description
            # record_exam.duration = exam_data_update.exam.duration
            # record_exam.school_year = exam_data_update.exam.school_year
            # record_exam.subject_id = exam_data_update.exam.subject_id
            # record_exam.grade_id = exam_data_update.exam.grade_id
            # record_exam.school_id = exam_data_update.exam.school_id
            # record_exam.subdivision_id = exam_data_update.exam.subdivision_id
            # record_exam.checkpoints = exam_data_update.exam.checkpoints
            # self.session_import.commit()

            # Update quiz question groups
            start_time = time.time()
            for quiz_question_group in exam_data_update.quiz_question_group_list:

                record_quiz_group = self.session_import.query(QuizQuestionGroup).filter(QuizQuestionGroup.id == quiz_question_group_id_mapping[quiz_question_group.id]).first()
                record_quiz_group.original_text = quiz_question_group.original_text
                record_quiz_group.parsed_text = quiz_question_group.parsed_text
                record_quiz_group.links = quiz_question_group.links
                self.session_import.commit()
            runtime = time.time() - start_time
            logging.info(f'Running {runtime:.15f} seconds: Update quiz question groups')

            # Update quiz questions
            start_time = time.time()
            order = 0
            for des_question_id, src_info_dict in id_mapping.items():
                idx, quiz_info_dict = self.get_index_by_value(exam_data_update.quiz_info_list, src_info_dict)
                update_item = exam_data_update.quiz_question_list[idx]
                record_quiz_question = self.session_import.query(QuizQuestion).filter(QuizQuestion.id == des_question_id).first()
                # record_quiz_question.quiz_question_group_id = update_item.quiz_question_group_id
                record_quiz_question.quiz_question_group_id = 0 if update_item.quiz_question_group_id==0 else quiz_question_group_id_mapping[update_item.quiz_question_group_id]
                record_quiz_question.original_text = update_item.original_text
                record_quiz_question.parsed_text = update_item.parsed_text
                record_quiz_question.quiz_type = update_item.quiz_type
                record_quiz_question.quiz_options = update_item.quiz_options
                record_quiz_question.explanation = update_item.explanation
                record_quiz_question.links = update_item.links
                record_quiz_question.quiz_answer = update_item.quiz_answer
                self.session_import.commit()
                logs = TrackingLogs(
                    src_exam_id = quiz_info_dict.get('src_exam_id'),
                    src_quiz_object_type = quiz_info_dict.get('src_quiz_object_type'),
                    src_quiz_question_id = quiz_info_dict.get('src_quiz_question_id'),
                    src_quiz_question_group_id = quiz_info_dict.get('src_quiz_question_group_id'),
                    des_exam_id = des_exam_id,
                    des_quiz_question_id = des_question_id,
                    des_quiz_question_group_id = 0 if update_item.quiz_question_group_id==0 else quiz_question_group_id_mapping[update_item.quiz_question_group_id],
                    task_name = 'update', # "insert", "update" or "delete"
                    order = order,
                )
                order += 1
                self.session_log.add(logs)
                self.session_log.commit()
            runtime = time.time() - start_time
            logging.info(f'Running {runtime:.15f} seconds: Update quiz questions')
            return des_exam_id
        return 0

@log_runtime
def sync_exam_bank(session_import: Session, session_log: Session, exam_id: int):
    exam_updater = ExamUpdater(session_import, session_log)
    exam_id = exam_updater.update_exam(exam_id)
    return exam_id