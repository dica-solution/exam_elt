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
    published_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    title = Column(String(150), nullable=False)
    banner_url = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    description_url = Column(String(255), nullable=True)
    price = Column(Integer, nullable=False)
    discount_price = Column(Integer, nullable=False)
    lecture_count = Column(Integer, nullable=False)
    grade_id = Column(Integer, nullable=False)
    subject_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    product_id = Column(String(255), nullable=False)

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
    parent_id = Column(BigInteger, nullable=False)
    published_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    level = Column(Integer, nullable=False)
    is_free = Column(Boolean, nullable=False)
    note_type = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)

class Lecture(Base):
    __tablename__ = 'lecture'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    title = Column(String(512), nullable=False)
    content_id = Column(BigInteger, nullable=False)
    content_type = Column(String(50), nullable=False)
    icon_url = Column(String(512), nullable=False)

class Theory(Base):
    __tablename__ = 'theory'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    title = Column(String(512), nullable=True)
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)

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
    user_id = Column(BigInteger, nullable=False)
    quiz_question_group_id = Column(Integer, nullable=False)
    original_text = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    quiz_type = Column(Integer, nullable=False)
    quiz_options = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    links = Column(Text, nullable=True)
    quiz_answer = Column(Text, nullable=True)
    level = Column(Integer, nullable=False)

class QuizCollectionGroup(Base):
    __tablename__ = 'quiz_collection_group'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    name = Column(String(50), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    grade_id = Column(Integer, nullable=False)
    subject_id = Column(Integer, nullable=False)
    quiz_count = Column(Integer, nullable=False)
    indicator = Column(Integer, nullable=False)
    type = Column(Integer, nullable=False)

class QuizCollection(Base):
    __tablename__ = 'quiz_collection'
    id = Column(BigInteger, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=func.now(), server_default=func.now())
    user_id = Column(BigInteger, nullable=False)
    quiz_id = Column(BigInteger, nullable=False)
    last_attempt_id = Column(BigInteger, nullable=False)
    quiz_collection_group_id = Column(BigInteger, nullable=False)
    sourse = Column(Integer, nullable=False)
    e_factor = Column(Float, nullable=False)
    interval = Column(Integer, nullable=False)
    repetition = Column(Integer, nullable=False)
    next_review_at = Column(DateTime, nullable=True)

class Media(Base):
    __tablename__ = 'media'
    id = Column(BigInteger, primary_key=True, nullable=False)
    name = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False)
    title = Column(String(512), nullable=False)
    caption = Column(Text, nullable=False)
    mine_type = Column(String(50), nullable=False)