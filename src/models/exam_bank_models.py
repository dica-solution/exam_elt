from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, Float, func, Text, Numeric, Boolean, BigInteger

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
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    original_text = Column(Text, nullable=False, default='')
    parsed_text = Column(Text, nullable=False, default='')
    links = Column(Text, nullable=False, default='')

class QuizQuestion(Base):
    __tablename__ = 'quiz_question'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, nullable=False, default=0)
    quiz_question_group_id = Column(Integer, nullable=False, default=0)
    original_text = Column(Text, nullable=False, default='')
    parsed_text = Column(Text, nullable=False, default='')
    quiz_type = Column(Integer, nullable=False, default=1)
    quiz_options = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True, default='')
    links = Column(Text, nullable=False, default='')
    quiz_answer = Column(Text, nullable=False)
    level = Column(Integer, nullable=False, default=0)


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


class SyncLogs(Base):
    __tablename__ = 'sync_logs'
    id = Column(Integer, primary_key=True, nullable=False)
    runtime = Column(DateTime, default=datetime.now(), server_default=func.now(), nullable=False)

class Course(Base):
    __tablename__ = 'course'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    published_at = Column(DateTime, nullable=True)
    title = Column(String(150), nullable=False, default='')
    banner_url = Column(String(255), nullable=False, default='')
    description = Column(Text, nullable=False, default='')
    description_url = Column(String(255), nullable=False, default='')
    price = Column(Integer, nullable=False, default=0)
    discount_price = Column(Integer, nullable=False, default=0)
    lecture_count = Column(Integer, nullable=False, default=0)
    grade_id = Column(Integer, nullable=False, default=0)
    subject_id = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, nullable=False, default=1)
    product_id = Column(String(255), nullable=False, default='')

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(150), nullable=False)
    status = Column(Boolean, nullable=False)

class CourseLecture(Base):
    __tablename__ = 'course_lecture'
    id = Column(BigInteger, primary_key=True, nullable=False)
    course_id = Column(BigInteger, nullable=False)
    lecture_id = Column(BigInteger, nullable=False)
    parent_id = Column(BigInteger, nullable=False, default=0)
    published_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    level = Column(Integer, nullable=False, default=0)
    is_free = Column(Boolean, nullable=False, default=False)
    node_type = Column(Integer, nullable=False, default=0)
    position = Column(Integer, nullable=False, default=0)

class Lecture(Base):
    __tablename__ = 'lecture'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    title = Column(String(512), nullable=False, default='')
    content_id = Column(BigInteger, nullable=False, default=0)
    content_type = Column(String(50), nullable=False, default='')
    icon_url = Column(String(512), nullable=False, default='')

class Theory(Base):
    __tablename__ = 'theory'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    title = Column(String(512), nullable=True)
    original_text = Column(Text, nullable=False, default='')
    parsed_text = Column(Text, nullable=False, default='')

class TheoryExample(Base):
    __tablename__ = 'theory_example'
    id = Column(BigInteger, primary_key=True, nullable=False)
    theory_id = Column(BigInteger, nullable=False)
    question_id = Column(BigInteger, nullable=False)
    position = Column(Integer, nullable=False)

class QuizCollectionGroup(Base):
    __tablename__ = 'quiz_collection_group'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    name = Column(String(50), nullable=False, default='')
    user_id = Column(BigInteger, nullable=False, default=0)
    grade_id = Column(Integer, nullable=False, default=0)
    subject_id = Column(Integer, nullable=False, default=0)
    quiz_count = Column(Integer, nullable=False, default=0)
    indicator = Column(Integer, nullable=False, default=0)
    type = Column(Integer, nullable=False, default=1)

class QuizCollection(Base):
    __tablename__ = 'quiz_collection'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, nullable=False, default=0)
    quiz_id = Column(BigInteger, nullable=False, default=0)
    last_attempt_id = Column(BigInteger, nullable=False, default=0)
    quiz_collection_group_id = Column(BigInteger, nullable=False, default=0)
    source = Column(Integer, nullable=False, default=0)
    e_factor = Column(Float, nullable=False, default=2.5)
    interval = Column(Integer, nullable=False, default=1)
    repetition = Column(Integer, nullable=False, default=0)
    next_review_at = Column(DateTime, nullable=True)

class Media(Base):
    __tablename__ = 'media'
    id = Column(BigInteger, primary_key=True, nullable=False)
    name = Column(String(512), nullable=False, default='')
    url = Column(String(512), nullable=False, default='')
    title = Column(String(512), nullable=False, default='')
    caption = Column(Text, nullable=False, default='')
    mine_type = Column(String(50), nullable=False, default='')

class CourseIDMapping(Base):
    __tablename__ = 'course_id_mapping'
    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    original_id = Column(Integer, nullable=False, default=0)
    new_id = Column(BigInteger, nullable=False)
    entity_type = Column(String(150), nullable=False)
    parent_new_id = Column(BigInteger, nullable=False, default=0)
    task_name = Column(String(50), nullable=False)