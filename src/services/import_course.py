from typing import List, Dict, Any, Optional
from src.models.exam_bank_models import CourseIDMapping
from src.services.logger_config import setup_logger
from src.services.processor import Processor
from src.services.import_exam import ImportExam

logger = setup_logger()



class ImportCourse:
    def __init__(self, session_import, 
                 session_log, 
                 settings):
        self.session_import = session_import
        self.session_log = session_log
        self.settings = settings
        self.processor = Processor(session_import, settings)
        self.exam_importer = ImportExam(session_import, session_log, settings)

    def create_course_id_mapping(self, original_id: int, new_id: int, entity_type: str, 
                                parent_new_id: int, position: int) -> CourseIDMapping:
        course_id_mapping = CourseIDMapping(
            original_id = original_id,
            new_id = new_id,
            entity_type = entity_type,
            parent_new_id = parent_new_id,
            position = position
        )
        logger.info(f"ID mapping: {parent_new_id} {entity_type}: {original_id} -> {new_id}")

        return course_id_mapping
    
    def import_course(self, course_id: int, is_free: bool=False):

        course_id_mapping_list = []
        current_position = 0
        lecture_count = 0

        course_data_dict = self.processor.get_data_dict(id=course_id, type='course')
        course = self.processor.process_course(course_data_dict)

        new_course_id = course.id

        for chapter_idx, chapter_dict in enumerate(course_data_dict.get('table_of_contents', [])):
            lecture_chapter = self.processor.process_lecture(lecture_data=chapter_dict, content_id=0, content_type='')
            self.session_import.add(lecture_chapter)

            new_chapter_id = lecture_chapter.id
            
            course_lecture_course_chapter, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_chapter_id, 
                                                                                                    parent_id=0, level=1, is_free=is_free, node_type=1, position=current_position)
            self.session_import.add(course_lecture_course_chapter)
            lecture_count += 1

            for lecture_idx, lecture_dict in enumerate(chapter_dict.get('course_lessons', [])):
                lecture_data_dict = self.processor.get_data_dict(id=lecture_dict.get('id'), type='lecture')
                lecture_lecture = self.processor.process_lecture(lecture_data=lecture_data_dict, content_id=0, content_type='')
                self.session_import.add(lecture_lecture)

                new_lecture_id = lecture_lecture.id

                course_lecture_chapter_lecture, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_id, 
                                                                                                         parent_id=course_lecture_course_chapter.id, 
                                                                                                         level=2, is_free=is_free, node_type=1, position=current_position)
                self.session_import.add(course_lecture_chapter_lecture)
                lecture_count += 1

                for content_idx, content_dict in enumerate(lecture_data_dict.get('content_types', [])):
                    if content_dict.get('__component') == 'course.overview':
                        theory = self.processor.process_theory(theory_data=content_dict)
                        self.session_import.add(theory)

                        lecture_lecture_theory = self.processor.process_lecture(lecture_data=content_dict, content_id=theory.id, content_type='theory')
                        self.session_import.add(lecture_lecture_theory)

                        new_lecture_id = lecture_lecture_theory.id

                        course_lecture_lecture_theory, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_id, 
                                                                                                                parent_id=course_lecture_chapter_lecture.id, 
                                                                                                                level=3, is_free=is_free, node_type=2, position=current_position)
                        self.session_import.add(course_lecture_lecture_theory)
                        lecture_count += 1

                    if content_dict.get('__component') == 'course.form':
                        for math_type_idx, math_type_dict in enumerate(content_dict.get('course_forms', [])):
                            math_type_data_dict = self.processor.get_data_dict(id=math_type_dict.get('id'), type='math_type')

                            lecture_math_type = self.processor.process_lecture(lecture_data=math_type_data_dict, content_id=0, content_type='')
                            self.session_import.add(lecture_math_type)

                            course_lecture_lecture_math_type, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_math_type.id, 
                                                                                                                     parent_id=course_lecture_chapter_lecture.id, 
                                                                                                                     level=3, is_free=is_free, node_type=1, position=current_position)
                            self.session_import.add(course_lecture_lecture_math_type)
                            lecture_count += 1

                            guide_dict = {
                                'title': 'Phương pháp giải',
                                'content': math_type_data_dict.get('guide', '')
                            }
                            guide = self.processor.process_theory(theory_data=guide_dict)
                            self.session_import.add(guide)

                            guide_data_dict = math_type_data_dict.copy()
                            guide_data_dict['title'] = guide_dict.get('title')
                            
                            lecture_math_type_guide = self.processor.process_lecture(lecture_data=guide_data_dict, content_id=guide.id, content_type='theory')
                            self.session_import.add(lecture_math_type_guide)

                            course_lecture_math_type_guide, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_math_type_guide.id,
                                                                                                                     parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                            self.session_import.add(course_lecture_math_type_guide)
                            lecture_count += 1

                            for example in math_type_data_dict.get('examples', []):
                                example_id = example.get('id')
                                example_data_dict = self.processor.get_data_dict(id=example_id, type='quiz_collection')
                                self.processor.process_theory_examples(theory_id=guide.id, question_item_list=example_data_dict.get('questions', []))

                            question_collection_data_list = []
                            for practice in math_type_data_dict.get('practices', []):
                                practice_id = practice.get('id')
                                practice_data_dict = self.processor.get_data_dict(id=practice_id, type='quiz_collection')
                                question_collection_data_list.extend(practice_data_dict.get('questions', []))
                            if question_collection_data_list:
                                collection_list = self.processor.process_practices(question_item_list=question_collection_data_list, grade_id=course.grade_id, subject_id=course.subject_id)
                                for collection in collection_list:
                                    collection_data_dict = practice_data_dict.copy()
                                    collection_data_dict['title'] = collection.name
                                    lecture_math_type_practice_collection = self.processor.process_lecture(lecture_data=collection_data_dict, content_id=collection.id, content_type='quizzes')
                                    self.session_import.add(lecture_math_type_practice_collection)

                                    course_lecture_math_type_practice_collection, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_math_type_practice_collection.id, 
                                                                                                                     parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                                    self.session_import.add(course_lecture_math_type_practice_collection)
                                    lecture_count += 1

                            guide_video_links = math_type_data_dict.get('guide_videos', [])
                            if guide_video_links:
                                for guide_video_link in guide_video_links:
                                    media = self.processor.process_media(media_data=guide_video_link)
                                    if media:
                                        self.session_import.add(media)
                                        guide_video_data_dict = math_type_data_dict.copy()
                                        guide_video_data_dict['title'] = 'Video'

                                        lecture_math_type_media = self.processor.process_lecture(lecture_data=guide_video_data_dict, content_id=media.id, content_type='video')
                                        self.session_import.add(lecture_math_type_media)

                                        course_lecture_math_type_media, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_math_type_media.id, 
                                                                                                                        parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                                        self.session_import.add(course_lecture_math_type_media)
                                        lecture_count += 1


                question_collection_data_list = []
                for question_collection in lecture_data_dict.get('practices', []):
                    question_collection_id = question_collection.get('id')
                    question_collection_data_dict = self.processor.get_data_dict(id=question_collection_id, type='quiz_collection')
                    question_collection_data_list.extend(question_collection_data_dict.get('questions', []))
                if question_collection_data_list:
                    collection_list =self.processor.process_practices(question_item_list=question_collection_data_list, grade_id=course.grade_id, subject_id=course.subject_id)
                    for collection in collection_list:
                        collection_data_dict = question_collection_data_dict.copy()
                        collection_data_dict['title'] = collection.name
                        lecture_practice_collection = self.processor.process_lecture(lecture_data=collection_data_dict, content_id=collection.id, content_type='quizzes')
                        self.session_import.add(lecture_practice_collection)

                        course_lecture_lecture_practice_collection, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_practice_collection.id, 
                                                                                                                     parent_id=course_lecture_chapter_lecture.id, level=3, is_free=is_free, node_type=2, position=current_position)
                        self.session_import.add(course_lecture_lecture_practice_collection)
                        lecture_count += 1

                
                exam_list = lecture_data_dict.get('paper_exams', [])
                if exam_list:
                    for exam in exam_list:
                        exam_id = exam.get('id')
                        imported_des_exam_id = self.exam_importer.import_exam(exam_id)

                        if imported_des_exam_id:
                            exam_data_dict = exam.copy()
                            exam_data_dict['title'] = 'Exam'
                            lecture_lecture_exam = self.processor.process_lecture(lecture_data=exam_data_dict, content_id=imported_des_exam_id, content_type='exams')
                            self.session_import.add(lecture_lecture_exam)

                            course_lecture_lecture_exam, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_lecture_exam.id, 
                                                                                                parent_id=course_lecture_chapter_lecture.id, level=4, is_free=is_free, node_type=2, position=current_position)
                            self.session_import.add(course_lecture_lecture_exam)
                            lecture_count += 1
                
                course.lecture_count = lecture_count
                self.session_import.add(course)
                self.session_import.commit()
        print(f"Imported course {course.id}")