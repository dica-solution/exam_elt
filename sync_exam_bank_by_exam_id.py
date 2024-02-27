import json
from typing import Any, Dict, List, Optional, Tuple
from commons import (
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
from exam_bank_models import (
    Exam,
    Uniqid,
    QuizQuestion,
    QuizQuestionGroup,
    ExamQuestion,
    TrackingLogs,
    Base,
)
from database import get_session_from_engine
from sqlalchemy import create_engine, and_, asc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine.base import Engine
import requests
import asyncio
import pandas as pd
import typer
from import_exam_bank_by_exam_id import PrepExamData, ExamParser

quizz_database_url = "postgresql://postgres:3FGae34ggFIg@dica-server:54321/exam_bank"
engine = create_engine(
    quizz_database_url,
    echo=False,
    pool_size=50,
    max_overflow=0,
)
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print(
            "Connection successful:", result.scalar()
        )  # If no error, connection established
except Exception as e:
    print("Connection failed:", e)


class ExamUpdater(ExamParser):
    def __init__(self, session: Session):
        super().__init__(session)

    def extract_data(self, page):
        auth_token = "90ada831257ab7d972cd7f2b7c8e84d604dc3c81e9c90537ab1d4707bf7aca57e67d31536162b1fe8650a1ed11b656a25e945d72181a4eb00b0dbe1caf4d3d8f5205c40f6eda47093663c59bad2d5c15ea0946174ffda0445697471a14bebeccc53873d5107d80f7e2897f753c4e2b2c45091bf1591edfe7dbad41ffb031bf6b"
        url = f"https://quizz.giainhanh.io/api/paper-exams/{page}?populate[0]=grade&populate[1]=subject&populate[3]=school&populate[4]=relatedItems.questionImages&populate[5]=relatedItems.relatedEssays&populate[6]=relatedItems.groupImages&populate[7]=relatedItems.relatedEntries&populate[8]=relatedItems.relatedEntries.questionImages&populate[9]=relatedItems.relatedQuizzes.questionImages&populate[10]=relatedItems.relatedEssays.questionImages"
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
        return dict()

    def get_destination_info(
        self, src_exam_id: int
    ) -> Tuple[int, List[int], Dict[int, int]]:
        result = (
            self.session.query(
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
        des_quiz_question_id_list = []
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
            # des_quiz_question_id_list.append(des_quiz_question_id)
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
        # return src_exam_id,
    
    def get_index_by_value(self, data_list, value_dict):
        # Make sure `inner_dict` are unique
        for index, item in enumerate(data_list):
            if item == value_dict:
                return index, item
        return None, dict()

    def update_exam(self, src_exam_id):
        des_exam_id, id_mapping, quiz_question_group_id_mapping = self.get_destination_info(src_exam_id)
        exam_data_update = self.parse_as_dict_collections(src_exam_id)
        if exam_data_update:
            # Update exam
            record_exam = self.session.query(Exam).filter(Exam.id == des_exam_id).first()
            record_exam.title = exam_data_update.exam.title
            record_exam.term = exam_data_update.exam.term
            record_exam.description = exam_data_update.exam.description
            record_exam.duration = exam_data_update.exam.duration
            record_exam.school_year = exam_data_update.exam.school_year
            record_exam.subject_id = exam_data_update.exam.subject_id
            record_exam.grade_id = exam_data_update.exam.grade_id
            record_exam.school_id = exam_data_update.exam.school_id
            record_exam.subdivision_id = exam_data_update.exam.subdivision_id
            record_exam.checkpoints = exam_data_update.exam.checkpoints
            self.session.commit()

            # Update quiz question groups
            for quiz_question_group in exam_data_update.quiz_question_group_list:
                record_quiz_group = self.session.query(QuizQuestionGroup).filter(QuizQuestionGroup.id == quiz_question_group_id_mapping[quiz_question_group.id]).first()
                record_quiz_group.original_text = quiz_question_group.original_text
                record_quiz_group.parsed_text = quiz_question_group.parsed_text
                record_quiz_group.links = quiz_question_group.links
                self.session.commit()

            # Update quiz questions
            order = 0
            for des_question_id, src_info_dict in id_mapping.items():
                idx, quiz_info_dict = self.get_index_by_value(exam_data_update.quiz_info_list, src_info_dict)
                update_item = exam_data_update.quiz_question_list[idx]
                record_quiz_question = self.session.query(QuizQuestion).filter(QuizQuestion.id == des_question_id).first()
                record_quiz_question.quiz_question_group_id = update_item.quiz_question_group_id
                record_quiz_question.original_text = update_item.original_text
                record_quiz_question.parsed_text = update_item.parsed_text
                record_quiz_question.quiz_type = update_item.quiz_type
                record_quiz_question.quiz_options = update_item.quiz_options
                record_quiz_question.explanation = update_item.explanation
                record_quiz_question.links = update_item.links
                record_quiz_question.quiz_answer = update_item.quiz_answer
                logs = TrackingLogs(
                    src_exam_id = quiz_info_dict.get('src_exam_id'),
                    src_quiz_object_type = quiz_info_dict.get('src_quiz_object_type'),
                    src_quiz_question_id = quiz_info_dict.get('src_quiz_question_id'),
                    src_quiz_question_group_id = quiz_info_dict.get('src_quiz_question_group_id'),
                    des_exam_id = des_exam_id,
                    des_quiz_question_id = des_question_id,
                    des_quiz_question_group_id = update_item.quiz_question_group_id,
                    task_name = 'update', # "insert", "update" or "delete"
                    order = order,
                )
                order += 1
                self.session.add(logs)
                self.session.commit()


def main(src_exam_id: int):
    with get_session_from_engine(engine) as session:
        exam_updater = ExamUpdater(session)
        exam_data_update = exam_updater.update_exam(src_exam_id)

if __name__=="__main__":
    typer.run(main)
