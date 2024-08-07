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
from src.config.config import get_settings
from datetime import datetime

settings = get_settings()

class ExamUpdater(ExamParser):
    def __init__(self, session_import: Session, session_log: Session,):
        super().__init__(session_import, session_log)

    def extract_data(self, exam_id):
        auth_token = settings.api_authentication_token
        url = settings.api_get_by_exam_id.format(EXAM_ID=exam_id)
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
        return dict()

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
    
    def check_changes(self, lastest_runtime, updated_time):
        # lastest_runtime = datetime.strptime(lastest_runtime, '%Y-%m-%d %H:%M:%S')
        updated_time = datetime.strptime(updated_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        if lastest_runtime < updated_time:
            return True
        else:
            return False

    def update_exam(self, src_exam_id, lastest_runtime):
        des_exam_id, id_mapping, quiz_question_group_id_mapping = self.get_destination_info(src_exam_id)
        exam_data_update = self.parse_as_dict_collections(src_exam_id)
        if exam_data_update:
            # Check if the exam has been updated
            # if 1:
            if self.check_changes(lastest_runtime, exam_data_update.exam.updated_at):
                # Update exam
                record_exam = self.session_import.query(Exam).filter(Exam.id == des_exam_id).first()
                record_exam.updated_at = exam_data_update.exam.updated_at
                self.session_import.commit()
                num_imported_quizzes = self.session_log.query(TrackingLogs).filter(
                    and_(
                        TrackingLogs.src_exam_id == src_exam_id,
                        TrackingLogs.task_name == "insert"
                    )
                ).count()
                if len(exam_data_update.quiz_question_list) == num_imported_quizzes: 
                    try:
                        # Update quiz question groups
                        for quiz_question_group in exam_data_update.quiz_question_group_list:
                            record_quiz_group = self.session_import.query(QuizQuestionGroup).filter(QuizQuestionGroup.id == quiz_question_group_id_mapping[quiz_question_group.id]).first()
                            record_quiz_group.original_text = quiz_question_group.original_text
                            record_quiz_group.parsed_text = quiz_question_group.parsed_text
                            record_quiz_group.links = quiz_question_group.links
                            self.session_import.commit()

                        # Update quiz questions
                        order = 0
                        update_mappings = []
                        for des_question_id, src_info_dict in id_mapping.items():
                            idx, quiz_info_dict = self.get_index_by_value(exam_data_update.quiz_info_list, src_info_dict)
                            update_item = exam_data_update.quiz_question_list[idx]

                            update_mapping = {
                                'id': des_question_id,
                                'quiz_question_group_id': 0 if update_item.quiz_question_group_id==0 else quiz_question_group_id_mapping[update_item.quiz_question_group_id],
                                'original_text': update_item.original_text,
                                'parsed_text': update_item.parsed_text,
                                'quiz_type': update_item.quiz_type,
                                'quiz_options': update_item.quiz_options,
                                'explanation': update_item.explanation,
                                'links': update_item.links,
                                'quiz_answer': update_item.quiz_answer,
                            }
                            update_mappings.append(update_mapping)
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
                        self.session_import.bulk_update_mappings(QuizQuestion, update_mappings)
                        self.session_import.commit()
                        self.session_log.commit()
                        return des_exam_id, None
                    except Exception as e:
                        self.session_import.rollback()
                        self.session_log.rollback()
                        return 0, e
                else:
                    try:
                        quiz_info_idx = 0
                        uniqid_idx = 1 # Ignore the first uniqid - exam
                        logs_list = []
                        # Register all related IDs for the current exam
                        uniqid_list = exam_data_update.uniqid_list
                        self.session_import.add_all(uniqid_list)
                        self.session_import.commit()

                        # Update exam info (num_quizzes)
                        des_exam_id = self.session_log.query(TrackingLogs.des_exam_id).filter(
                            and_(
                                TrackingLogs.src_exam_id == src_exam_id,
                                TrackingLogs.task_name == "insert"
                            )
                        ).first()[0]
                        self.session_import.query(Exam).filter(Exam.id == des_exam_id).update({Exam.num_quizzes: len(exam_data_update.quiz_question_list)})

                        # Update exam_id values of question have that des_exam_id is zero
                        self.session_import.query(ExamQuestion).filter(ExamQuestion.exam_id == des_exam_id).update({ExamQuestion.exam_id: 0})

                        exam = self.session_import.query(Exam).filter(Exam.id == des_exam_id).first()
                        exam.num_quizzes = len(exam_data_update.quiz_question_list)
                        self.session_import.commit()

                        # Store all quiz_question_group_list
                        ref_quiz_groups = dict()
                        quiz_question_group_list = exam_data_update.quiz_question_group_list
                        for group in quiz_question_group_list:
                            group_id = group.id
                            group.id = None
                            self.session_import.add(group)
                            self.session_import.commit()
                            ref_quiz_groups[group_id] = group.id

                        # Specify realted quizzes and store them
                        quiz_question_list = exam_data_update.quiz_question_list
                        for idx, quiz in enumerate(quiz_question_list):
                            quiz.id = uniqid_list[uniqid_idx].to_uniqid_number()
                            uniqid_idx += 1
                            ref_group_id = quiz.quiz_question_group_id
                            if ref_group_id:
                                quiz.quiz_question_group_id = ref_quiz_groups[ref_group_id]
                            quiz_info_dict = exam_data_update.quiz_info_list[quiz_info_idx]
                            quiz_info_idx += 1
                            logs_list.append(TrackingLogs(
                                src_exam_id = quiz_info_dict.get('src_exam_id'),
                                src_quiz_object_type = quiz_info_dict.get('src_quiz_object_type'),
                                src_quiz_question_id = quiz_info_dict.get('src_quiz_question_id'),
                                src_quiz_question_group_id = quiz_info_dict.get('src_quiz_question_group_id'),
                                des_exam_id = des_exam_id,
                                des_quiz_question_id = quiz.id,
                                des_quiz_question_group_id = quiz.quiz_question_group_id,
                                task_name = 'update', # "insert", "update"
                                order = idx,
                            ))
                        self.session_import.add_all(quiz_question_list)
                        self.session_import.commit()
                        self.session_log.add_all(logs_list)
                        self.session_log.commit()

                        exam_question_list = []
                        for idx, question in enumerate(quiz_question_list):
                            exam_question = ExamQuestion(exam_id=des_exam_id,
                                                        quiz_question_id=question.id,
                                                        order=idx,
                                                        is_checkpoint=False)
                            exam_question_list.append(exam_question)
                        self.session_import.add_all(exam_question_list)
                        self.session_import.commit()
                        return exam.id, None
                    except Exception as e:
                        self.session_import.rollback()
                        self.session_log.rollback()
                        return 0, e
            else:
                return -1, None

def sync_exam_bank(session_import: Session, session_log: Session, exam_id: int, lastest_runtime: str):
    exam_updater = ExamUpdater(session_import, session_log)
    exam_id, error = exam_updater.update_exam(exam_id, lastest_runtime)
    return exam_id, error