from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, func, Text, Numeric, Boolean, BigInteger

from src.database import Base


class Exam(Base):
    __tablename__ = 'exam'
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    created_by = Column(BigInteger, default=1)
    updated_by = Column(BigInteger, default=1)

    title = Column(String(255))
    term = Column(String(255))
    description = Column(Text, nullable=True)
    duration = Column(Integer)
    school_year = Column(String(255))
    subject_id = Column(Integer)
    grade_id = Column(Integer)
    school_id = Column(Integer)
    subdivision_id = Column(Integer)
    checkpoints = Column(Integer)
    num_quizzes = Column(Integer)

    published_at = Column(DateTime, default=datetime.now(), server_default=func.now())


class ExamQuestion(Base):
    __tablename__ = 'exam_question'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    exam_id = Column(BigInteger)
    quiz_question_id = Column(BigInteger)
    order = Column(Integer)
    is_checkpoint = Column(Boolean)


class QuizQuestionGroup(Base):
    __tablename__ = 'quiz_question_group'
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    links = Column(Text, nullable=True) # {"audio_links": [], "video_links": [], "image_links": []}


class QuizQuestion(Base):
    __tablename__ = 'quiz_question'
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, default=1)
    quiz_question_group_id = Column(Integer)
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    quiz_type = Column(Integer)
    quiz_options = Column(Text, nullable=True) # {"label": "A", "content": "sample content", "is_correct": true}
    explanation = Column(Text, nullable=True)
    links = Column(Text, nullable=True) # {"audio_links": [], "video_links": [], "image_links": []}
    quiz_answer = Column(Text, nullable=True)


class Uniqid(Base):
    __tablename__ = 'uniqid'
    id = Column(Integer, primary_key=True)
    uniqid_type = Column(Integer)

    def to_uniqid_number(self):
        return int(f"1{self.uniqid_type:03d}{self.id:013d}")


class TrackingLogs(Base):
    __tablename__ = 'tracking_logs'
    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, default=datetime.now(), server_default=func.now())
    src_exam_id = Column(Integer)
    # src_quiz_object_type = Column(String(255))
    src_quiz_object_type = Column(Integer)
    src_quiz_question_id = Column(Integer)
    src_quiz_question_group_id = Column(Integer)
    des_exam_id = Column(BigInteger)
    des_quiz_question_id = Column(BigInteger)
    des_quiz_question_group_id = Column(Integer)
    task_name = Column(String(255)) # "insert", "update" or "delete"
    # status = Column(String(255))
    order = Column(Integer)