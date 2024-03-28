from sqlalchemy import Column, Integer, Text, ForeignKey, create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from src.config.config import settings
import json

Base = declarative_base()

class Chapter(Base):
    __tablename__ = 'chapter'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    grade_id = Column(Integer)
    subject_id = Column(Integer)
    problems = relationship('ProblemType', backref='chapter', lazy=True)

class ProblemType(Base):
    __tablename__ = 'problem_type'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    solution_steps = Column(Text)
    chapter_id = Column(Integer, ForeignKey('chapter.id'))

engine = create_engine("postgresql://postgres:3FGae34ggFIg@dica-server:54321/maths_knowledge_base")
Session = sessionmaker(bind=engine)
session = Session()

# chapters = session.query(Chapter).all()
# for chapter in chapters:
#     print(chapter.name)

file_path = "test.json"
with open(file_path, "r") as json_file:
    data = json.load(json_file)

grade_id=1
subject_id=1

for item in data:
    chapter = session.query(Chapter).filter(Chapter.name == item['chapter']).first()
    if not chapter:
        chapter = Chapter(name=item['chapter'], grade_id=grade_id, subject_id=subject_id)
        session.add(chapter)
        session.commit()
    for problem_type in item['problem_types']:
        problem = ProblemType(name=problem_type['problem_type'], solution_steps=problem_type['solution_steps'], chapter_id=chapter.id)
        session.add(problem)
        session.commit()
    

print("Hello")