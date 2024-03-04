from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, func, Text, Numeric, Boolean, BigInteger

from src.database import Base


class Exam(Base):
    __tablename__ = 'exam'
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    created_by = Column(BigInteger, default=1, nullable=False)
    updated_by = Column(BigInteger, default=1, nullable=False)

    title = Column(String(255), nullable=False)
    term = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)
    school_year = Column(String(255), nullable=False)
    subject_id = Column(Integer, nullable=False)
    grade_id = Column(Integer, nullable=False)
    school_id = Column(Integer, nullable=False)
    subdivision_id = Column(Integer, nullable=False)
    checkpoints = Column(Integer, nullable=False)
    num_quizzes = Column(Integer, nullable=False)

    published_at = Column(DateTime, default=datetime.now(), server_default=func.now())


class ExamQuestion(Base):
    __tablename__ = 'exam_question'
    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    exam_id = Column(BigInteger, nullable=False)
    quiz_question_id = Column(BigInteger, nullable=False)
    order = Column(Integer, nullable=False)
    is_checkpoint = Column(Boolean, nullable=False)


class QuizQuestionGroup(Base):
    __tablename__ = 'quiz_question_group'
    id = Column(Integer, primary_key=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    links = Column(Text, nullable=True) # {"audio_links": [], "video_links": [], "image_links": []}


class QuizQuestion(Base):
    __tablename__ = 'quiz_question'
    id = Column(Integer, primary_key=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, default=1, nullable=False)
    quiz_question_group_id = Column(Integer, nullable=False)
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    quiz_type = Column(Integer, nullable=False)
    quiz_options = Column(Text, nullable=True) # {"label": "A", "content": "sample content", "is_correct": true}
    explanation = Column(Text, nullable=True)
    links = Column(Text, nullable=True) # {"audio_links": [], "video_links": [], "image_links": []}
    quiz_answer = Column(Text, nullable=True)


class Uniqid(Base):
    __tablename__ = 'uniqid'
    id = Column(Integer, primary_key=True, nullable=False)
    uniqid_type = Column(Integer, nullable=False)

    def to_uniqid_number(self):
        return int(f"1{self.uniqid_type:03d}{self.id:013d}")


class TrackingLogs(Base):
    __tablename__ = 'tracking_logs'
    id = Column(Integer, primary_key=True, nullable=False)

    timestamp = Column(DateTime, default=datetime.now(), server_default=func.now())
    src_exam_id = Column(Integer, nullable=False)
    # src_quiz_object_type = Column(String(255))
    src_quiz_object_type = Column(Integer, nullable=False)
    src_quiz_question_id = Column(Integer, nullable=False)
    src_quiz_question_group_id = Column(Integer, nullable=False)
    des_exam_id = Column(BigInteger, nullable=False)
    des_quiz_question_id = Column(BigInteger, nullable=False)
    des_quiz_question_group_id = Column(Integer, nullable=False)
    task_name = Column(String(255), nullable=False) # "insert", "update" or "delete"
    # status = Column(String(255))
    order = Column(Integer, nullable=False)