from typing import List, Dict, Any, Optional
from src.models.exam_bank_models import CourseIDMapping
from src.services.logger_config import setup_logger
from src.services.processor import Processor
from src.services.import_exam import ImportExam

logger = setup_logger()
logger.info("Import course...")



class ImportCourse:
    def __init__(self, session_import, 
                 session_log, 
                 settings):
        self.session_import = session_import
        self.session_log = session_log
        self.settings = settings
        self.processor = Processor(session_import, settings)
        self.exam_importer = ImportExam(session_import, session_log, settings)

    
    def import_course(self, course_id: int, is_free: bool=False):

        course_id_mapping_list = []
        current_position = 0
        lecture_count = 0

        course_data_dict = self.processor.get_data_dict(id=course_id, type='course')
        course = self.processor.process_course(course_data_dict)

        new_course_id = course.id

        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=course_id, new_id=new_course_id, 
                                                                              entity_type='course', parent_new_id=0, task_name='insert'))

        chapters = course_data_dict.get('table_of_contents', [])
        # print(len(chapters))
        if chapters:
            for chapter_idx, chapter_dict in enumerate(chapters):
                
                lecture_chapter = self.processor.process_lecture(lecture_data=chapter_dict, content_id=0, content_type='')
                self.session_import.add(lecture_chapter)

                new_chapter_id = lecture_chapter.id
                
                course_lecture_course_chapter, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_chapter_id, 
                                                                                                        parent_id=0, level=1, is_free=is_free, node_type=1, position=current_position)
                self.session_import.add(course_lecture_course_chapter)
                self.session_import.flush()
                lecture_count += 1

                course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=chapter_dict.get('id'), new_id=course_lecture_course_chapter.id,
                                                                                      entity_type='chapter', parent_new_id=new_course_id, task_name='insert'))

                lessons = chapter_dict.get('course_lessons', [])
                if lessons:
                    for lecture_idx, lecture_dict in enumerate(lessons):
                        lecture_data_dict = self.processor.get_data_dict(id=lecture_dict.get('id'), type='lecture')
                        lecture_lecture = self.processor.process_lecture(lecture_data=lecture_data_dict, content_id=0, content_type='')
                        self.session_import.add(lecture_lecture)

                        new_lecture_id = lecture_lecture.id

                        course_lecture_chapter_lecture, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_id, 
                                                                                                                parent_id=course_lecture_course_chapter.id, 
                                                                                                                level=2, is_free=is_free, node_type=1, position=current_position)
                        self.session_import.add(course_lecture_chapter_lecture)
                        self.session_import.flush()
                        lecture_count += 1

                        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=lecture_dict.get('id'), new_id=course_lecture_chapter_lecture.id,
                                                                                              entity_type='lecture', parent_new_id=course_lecture_course_chapter.id, task_name='insert'))
                        
                        contents = lecture_data_dict.get('content_types', [])
                        if contents:
                            for content_idx, content_dict in enumerate(contents):
                                if content_dict.get('__component') == 'course.overview':
                                    theory = self.processor.process_theory(theory_data=content_dict)
                                    self.session_import.add(theory)

                                    lecture_lecture_theory = self.processor.process_lecture(lecture_data=content_dict, content_id=theory.id, content_type='theory')
                                    self.session_import.add(lecture_lecture_theory)

                                    new_lecture_theory_id = lecture_lecture_theory.id

                                    course_lecture_lecture_theory, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_theory_id, 
                                                                                                                            parent_id=course_lecture_chapter_lecture.id, 
                                                                                                                            level=3, is_free=is_free, node_type=2, position=current_position)
                                    self.session_import.add(course_lecture_lecture_theory)
                                    self.session_import.flush()
                                    lecture_count += 1

                                    course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=content_dict.get('id'), new_id=course_lecture_lecture_theory.id,
                                                                                                          entity_type='theory', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))

                                if content_dict.get('__component') == 'course.form':
                                    course_forms = content_dict.get('course_forms', [])
                                    if course_forms:
                                        for math_type_idx, math_type_dict in enumerate(course_forms):
                                            math_type_data_dict = self.processor.get_data_dict(id=math_type_dict.get('id'), type='math_type')

                                            lecture_math_type = self.processor.process_lecture(lecture_data=math_type_data_dict, content_id=0, content_type='')
                                            self.session_import.add(lecture_math_type)
                                            new_lecture_math_type_id = lecture_math_type.id

                                            course_lecture_lecture_math_type, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_math_type_id, 
                                                                                                                                    parent_id=course_lecture_chapter_lecture.id, 
                                                                                                                                    level=3, is_free=is_free, node_type=1, position=current_position)
                                            self.session_import.add(course_lecture_lecture_math_type)
                                            self.session_import.flush()
                                            lecture_count += 1

                                            course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=math_type_data_dict.get('id'), new_id=course_lecture_lecture_math_type.id,
                                                                                                                  entity_type='math_type', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))

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
                                            
                                            new_lecture_math_type_guide_id = lecture_math_type_guide.id

                                            course_lecture_math_type_guide, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_math_type_guide_id,
                                                                                                                                    parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                                            self.session_import.add(course_lecture_math_type_guide)
                                            self.session_import.flush()
                                            lecture_count += 1

                                            course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=0, new_id=course_lecture_math_type_guide.id,
                                                                                                                  entity_type='guide', parent_new_id=course_lecture_lecture_math_type.id, task_name='insert'))

                                            examples = math_type_data_dict.get('examples', [])
                                            if examples:
                                                for example in examples:
                                                    example_id = example.get('id')
                                                    example_data_dict = self.processor.get_data_dict(id=example_id, type='quiz_collection')
                                                    question_id_mapping_list = self.processor.process_theory_examples(theory_id=guide.id, course_lecture_id=course_lecture_math_type_guide.id, 
                                                                                           question_item_list=example_data_dict.get('questions', []))
                                                    course_id_mapping_list.extend(question_id_mapping_list)

                                                question_collection_data_list = []

                                            practices = math_type_data_dict.get('practices', [])
                                            if practices:
                                                for practice in math_type_data_dict.get('practices', []):
                                                    practice_id = practice.get('id')
                                                    practice_data_dict = self.processor.get_data_dict(id=practice_id, type='quiz_collection')
                                                    question_collection_data_list.extend(practice_data_dict.get('questions', []))
                                                if question_collection_data_list:
                                                    collection_list = self.processor.process_practices(question_item_list=question_collection_data_list, grade_id=course.grade_id, subject_id=course.subject_id)
                                                    for item in collection_list:
                                                        collection = item[0]
                                                        question_ids_list = item[1]
                                                        collection_data_dict = practice_data_dict.copy()
                                                        collection_data_dict['title'] = collection.name
                                                        lecture_math_type_practice_collection = self.processor.process_lecture(lecture_data=collection_data_dict, content_id=collection.id, content_type='quizzes')
                                                        self.session_import.add(lecture_math_type_practice_collection)

                                                        course_lecture_math_type_practice_collection, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_math_type_practice_collection.id, 
                                                                                                                                        parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                                                        self.session_import.add(course_lecture_math_type_practice_collection)
                                                        self.session_import.flush()
                                                        lecture_count += 1

                                                        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=0, new_id=course_lecture_math_type_practice_collection.id, entity_type='collection',
                                                                                                                              parent_new_id=course_lecture_lecture_math_type.id, task_name='insert'))

                                                        for question_ids in question_ids_list:
                                                            course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=question_ids[0], new_id=question_ids[1], entity_type='question',
                                                                                                                              parent_new_id=course_lecture_math_type_practice_collection.id, task_name='insert'))

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

                                                        new_lecture_math_type_media_id = lecture_math_type_media.id

                                                        course_lecture_math_type_media, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=new_lecture_math_type_media_id, 
                                                                                                                                        parent_id=course_lecture_lecture_math_type.id, level=4, is_free=is_free, node_type=2, position=current_position)
                                                        self.session_import.add(course_lecture_math_type_media)
                                                        self.session_import.flush()
                                                        lecture_count += 1

                                                        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=guide_video_link.get('id'), new_id=course_lecture_math_type_media.id,
                                                                                                                              entity_type='media', parent_new_id=course_lecture_lecture_math_type.id, task_name='insert'))


                        # question_collection_data_list = []
                        # practices = lecture_data_dict.get('practices', [])
                        # if practices:
                        #     for question_collection in practices:
                        #         question_collection_id = question_collection.get('id')
                        #         question_collection_data_dict = self.processor.get_data_dict(id=question_collection_id, type='quiz_collection')
                        #         questions = question_collection_data_dict.get('questions')
                        #         if questions:
                        #             question_collection_data_list.extend(questions)
                        #     if question_collection_data_list:
                        #         collection_list =self.processor.process_practices(question_item_list=question_collection_data_list, grade_id=course.grade_id, subject_id=course.subject_id)
                        #         for collection in collection_list:
                        #             collection_data_dict = question_collection_data_dict.copy()
                        #             collection_data_dict['title'] = collection.name
                        #             lecture_practice_collection = self.processor.process_lecture(lecture_data=collection_data_dict, content_id=collection.id, content_type='quizzes')
                        #             self.session_import.add(lecture_practice_collection)

                        #             course_lecture_lecture_practice_collection, current_position = self.processor.process_course_lecture(course_id=new_course_id, lecture_id=lecture_practice_collection.id, 
                        #                                                                                                         parent_id=course_lecture_chapter_lecture.id, level=3, is_free=is_free, node_type=2, position=current_position)
                        #             self.session_import.add(course_lecture_lecture_practice_collection)
                        #             lecture_count += 1

                        
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
                                                                                                        parent_id=course_lecture_chapter_lecture.id, level=3, is_free=is_free, node_type=2, position=current_position)
                                    self.session_import.add(course_lecture_lecture_exam)
                                    self.session_import.flush()
                                    lecture_count += 1

                                    course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=exam_id, new_id=course_lecture_lecture_exam.id,
                                                                                                          entity_type='exam', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))

                print(chapter_dict.get('title'))

        course.lecture_count = lecture_count
        self.session_import.add(course)
        self.session_import.add_all(course_id_mapping_list)
        self.session_import.commit()
        logger.info(f"Imported course {course.id}")
        print(f"Imported course {course.id}")
