from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean, BigInteger, func
from src.database import Base

class Uniqid(Base):
    __tablename__ = 'uniqid'
    id = Column(Integer, primary_key=True, nullable=False)
    uniqid_type = Column(Integer, nullable=False)

    def to_uniqid_number(self):
        return int(f"1{self.uniqid_type:03d}{self.id:013d}")
    
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

class QuizQuestion(Base):
    __tablename__ = 'quiz_question'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, nullable=False, default=0)
    quiz_question_group_id = Column(Integer, nullable=False, default=0)
    original_text = Column(Text, nullable=False)
    parsed_text = Column(Text, nullable=False)
    quiz_type = Column(Integer, nullable=False)
    quiz_options = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True, default='')
    links = Column(Text, nullable=False)
    quiz_answer = Column(Text, nullable=False)
    level = Column(Integer, nullable=False, default=0)

class QuizQuestionGroup(Base):
    __tablename__ = 'quiz_question_group'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    original_text = Column(Text, nullable=False)
    parsed_text = Column(Text, nullable=False)
    link = Column(Text, nullable=False)

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
    name = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False)
    title = Column(String(512), nullable=False)
    caption = Column(Text, nullable=False)
    mine_type = Column(String(50), nullable=False)

