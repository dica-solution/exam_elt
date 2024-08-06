from src.services.logger_config import setup_logger
from src.services.processor import Processor
from src.services.import_exam import ImportExam
from datetime import datetime
from src.models.exam_bank_models import CourseIDMapping, CourseLecture, Lecture, Media, Course
from src.commons import *
from typing import List
from sqlalchemy import update

logger = setup_logger()

class Utils:
    def __init__(self, session_import, session_log, settings):
        self.session_import = session_import
        self.session_log = session_log
        self.settings = settings
        self.processor = Processor(session_import, settings)
        self.exam_importer = ImportExam(session_import, session_log, settings)
        # self.processor = processor

    # Import utils

    def _add_guide_video(self, course, course_lecture_lecture_math_type, math_type_data_dict, is_free, lecture_count, current_position, level=4):
        course_id_mapping_list = []
        guide_video_links = math_type_data_dict.get('guide_videos')
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

                    course_lecture_math_type_media, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=new_lecture_math_type_media_id, 
                                                                                                             parent_id=course_lecture_lecture_math_type.id, level=level, is_free=is_free, 
                                                                                                             node_type=2, position=current_position)
                    self.session_import.add(course_lecture_math_type_media)
                    self.session_import.flush()
                    lecture_count += 1

                    course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=guide_video_link.get('id'), new_id=course_lecture_math_type_media.id, 
                                                                                          entity_type='media', parent_new_id=course_lecture_lecture_math_type.id, task_name='insert'))        

        return course_id_mapping_list, lecture_count, current_position

    def _add_guide_theory_and_examples(self, course, course_lecture_lecture_math_type, math_type_data_dict, lecture_count, is_free, current_position, level=4):
        course_id_mapping_list = []
        guide_content = math_type_data_dict.get('guide')
        examples = math_type_data_dict.get('examples')
        if not guide_content and not examples:
            logger.info("Empty guide and examples")
        else:
            guide_dict = {
                'title': 'Lý thuyết kèm ví dụ mẫu',
                'content': guide_content
            }
            guide = self.processor.process_theory(theory_data=guide_dict)
            self.session_import.add(guide)

            guide_data_dict = math_type_data_dict.copy()
            guide_data_dict['title'] = guide_dict.get('title')
            
            lecture_math_type_guide = self.processor.process_lecture(lecture_data=guide_data_dict, content_id=guide.id, content_type='theory')
            self.session_import.add(lecture_math_type_guide)
            
            new_lecture_math_type_guide_id = lecture_math_type_guide.id

            course_lecture_math_type_guide, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=new_lecture_math_type_guide_id,
                                                                                                     parent_id=course_lecture_lecture_math_type.id, level=level, is_free=is_free, 
                                                                                                     node_type=2, position=current_position)
            self.session_import.add(course_lecture_math_type_guide)
            self.session_import.flush()
            lecture_count += 1

            course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=0, new_id=course_lecture_math_type_guide.id,
                                                                                entity_type='guide', parent_new_id=course_lecture_lecture_math_type.id, task_name='insert'))

            if examples:
                for example in examples:
                    example_id = example.get('id')
                    example_data_dict = self.processor.get_data_dict(id=example_id, type='quiz_collection')
                    question_id_mapping_list = self.processor.process_theory_examples(theory_id=guide.id, course_lecture_id=course_lecture_math_type_guide.id, 
                                                        question_item_list=example_data_dict.get('questions', []))
                    course_id_mapping_list.extend(question_id_mapping_list)

        return course_id_mapping_list, lecture_count, current_position

    def _add_practice_collections(self, course, course_lecture, data_dict, lecture_count, is_free, current_position, level):
        course_id_mapping_list = []
        question_collection_data_list = []
        practices = data_dict.get('practices')
        if practices:
            for practice in practices:
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

                    course_lecture_math_type_practice_collection, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=lecture_math_type_practice_collection.id, 
                                                                                                    parent_id=course_lecture.id, level=level, is_free=is_free, node_type=2, position=current_position)
                    self.session_import.add(course_lecture_math_type_practice_collection)
                    self.session_import.flush()
                    lecture_count += 1

                    course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=0, new_id=course_lecture_math_type_practice_collection.id, entity_type='collection',
                                                                                        parent_new_id=course_lecture.id, task_name='insert'))

                    for question_ids in question_ids_list:
                        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=question_ids[0], new_id=question_ids[1], entity_type='question',
                                                                                        parent_new_id=course_lecture_math_type_practice_collection.id, task_name='insert'))
        
        return course_id_mapping_list, lecture_count, current_position

    def _add_exams(self, course, course_lecture_chapter_lecture, lecture_data_dict, lecture_count, is_free, current_position):
        course_id_mapping_list = []
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

                    course_lecture_lecture_exam, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=lecture_lecture_exam.id, 
                                                                                        parent_id=course_lecture_chapter_lecture.id, level=3, is_free=is_free, node_type=2, position=current_position)
                    self.session_import.add(course_lecture_lecture_exam)
                    self.session_import.flush()
                    lecture_count += 1

                    course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=exam_id, new_id=course_lecture_lecture_exam.id,
                                                                                        entity_type='exam', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))        
        return course_id_mapping_list, lecture_count, current_position
    
    def _add_math_type(self, course, course_lecture_chapter_lecture, content_dict, lecture_count, is_free, current_position):
        course_id_mapping_list = []
        course_forms = content_dict.get('course_forms', [])
        if course_forms:
            for math_type_idx, math_type_dict in enumerate(course_forms):
                math_type_data_dict = self.processor.get_data_dict(id=math_type_dict.get('id'), type='math_type')

                lecture_math_type = self.processor.process_lecture(lecture_data=math_type_data_dict, content_id=0, content_type='')
                self.session_import.add(lecture_math_type)
                new_lecture_math_type_id = lecture_math_type.id

                course_lecture_lecture_math_type, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=new_lecture_math_type_id, 
                                                                                                        parent_id=course_lecture_chapter_lecture.id, 
                                                                                                        level=3, is_free=is_free, node_type=1, position=current_position)
                self.session_import.add(course_lecture_lecture_math_type)
                self.session_import.flush()
                lecture_count += 1

                course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=math_type_data_dict.get('id'), new_id=course_lecture_lecture_math_type.id,
                                                                                    entity_type='math_type', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))
                
                id_mapping_list, lecture_count, current_position = self._add_guide_video(course, course_lecture_lecture_math_type, math_type_data_dict, is_free,
                                                                                         lecture_count, current_position, level=4)
                course_id_mapping_list.extend(id_mapping_list)

                id_mapping_list, lecture_count, current_position = self._add_guide_theory_and_examples(course, course_lecture_lecture_math_type, math_type_data_dict,
                                                                                                       lecture_count, is_free, current_position, level=4)
                course_id_mapping_list.extend(id_mapping_list)

                id_mapping_list, lecture_count, current_position = self._add_practice_collections(course, course_lecture_lecture_math_type, math_type_data_dict, 
                                                                                                  lecture_count, is_free, current_position, level=4)
                course_id_mapping_list.extend(id_mapping_list)

            return course_id_mapping_list, lecture_count, current_position
       
    def _add_lesson(self, course, course_lecture_course_chapter, lecture_dict, lecture_count, is_free, current_position, level=2):
        course_id_mapping_list = []
        # lessons = chapter_dict.get('course_lessons')
        # if lessons:
        #     for lecture_idx, lecture_dict in enumerate(lessons):
        lecture_data_dict = self.processor.get_data_dict(lecture_dict.get('id'), 'lecture')
        published_flag = lecture_data_dict.get('publishedAt')
        if published_flag:
            lecture_lecture = self.processor.process_lecture(lecture_data_dict, 0, '')
            self.session_import.add(lecture_lecture)
            new_lecture_id = lecture_lecture.id
            course_lecture_chapter_lecture, current_position = self.processor.process_course_lecture(course.id, new_lecture_id, course_lecture_course_chapter.id, 
                                                                                                        level, is_free, 1, current_position)
            self.session_import.add(course_lecture_chapter_lecture)
            self.session_import.flush()
            lecture_count += 1

            course_id_mapping_list.append(self.processor.create_course_id_mapping(lecture_dict.get('id'), course_lecture_chapter_lecture.id,
                                                                                    'lecture', course_lecture_course_chapter.id, 'insert'))
            contents = lecture_data_dict.get('content_types')
            if contents:
                for content_idx, content_dict in enumerate(contents):
                    if content_dict.get('__component') == 'course.overview':
                        theory = self.processor.process_theory(content_dict)
                        self.session_import.add(theory)

                        lecture_lecture_theory = self.processor.process_lecture(lecture_data=content_dict, content_id=theory.id, content_type='theory')
                        self.session_import.add(lecture_lecture_theory)

                        new_lecture_theory_id = lecture_lecture_theory.id

                        course_lecture_lecture_theory, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=new_lecture_theory_id, 
                                                                                                                parent_id=course_lecture_chapter_lecture.id, 
                                                                                                                level=3, is_free=is_free, node_type=2, position=current_position)
                        self.session_import.add(course_lecture_lecture_theory)
                        self.session_import.flush()
                        lecture_count += 1

                        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=content_dict.get('id'), new_id=course_lecture_lecture_theory.id,
                                                                                            entity_type='theory', parent_new_id=course_lecture_chapter_lecture.id, task_name='insert'))
                    if content_dict.get('__component') == 'course.form':
                        id_mapping_list, lecture_count, current_position = self._add_math_type(course, course_lecture_chapter_lecture, content_dict,
                                                                                                lecture_count, is_free, current_position)
                        course_id_mapping_list.extend(id_mapping_list)
            id_mapping_list, lecture_count, current_position = self._add_practice_collections(course, course_lecture_chapter_lecture, lecture_data_dict, lecture_count, is_free, current_position, level=3)
            course_id_mapping_list.extend(id_mapping_list)

            id_mapping_list, lecture_count, current_position = self._add_exams(course, course_lecture_chapter_lecture, lecture_data_dict, lecture_count, is_free, current_position)
            course_id_mapping_list.extend(id_mapping_list)

            return course_id_mapping_list, lecture_count, current_position

    def _add_chapter(self, course, chapter_dict, lecture_count, is_free, current_position):
        course_id_mapping_list = []
        # chapters = course_data_dict.get('table_of_contents')
        # if chapters:
        #     for chapter_dict in chapters:
        lecture_chapter = self.processor.process_lecture(lecture_data=chapter_dict, content_id=0, content_type='')
        self.session_import.add(lecture_chapter)
        new_chapter_id = lecture_chapter.id
        course_lecture_course_chapter, current_position = self.processor.process_course_lecture(course_id=course.id, lecture_id=new_chapter_id, 
                                                                                            parent_id=0, level=1, is_free=is_free, node_type=1, position=current_position)
        self.session_import.add(course_lecture_course_chapter)
        self.session_import.flush()
        lecture_count += 1

        course_id_mapping_list.append(self.processor.create_course_id_mapping(original_id=chapter_dict.get('id'), new_id=course_lecture_course_chapter.id,
                                                                            entity_type='chapter', parent_new_id=course.id, task_name='insert'))
        
        lessons = chapter_dict.get('course_lessons')
        if lessons:
            for lecture_dict in lessons:
                id_mapping_list, lecture_count, current_position = self._add_lesson(course, course_lecture_course_chapter, lecture_dict, lecture_count, is_free, current_position)
                course_id_mapping_list.extend(id_mapping_list)

        return course_id_mapping_list, lecture_count, current_position





    # Update utils

    def _get_course_id(self, original_course_id):
        course_id = self.session_import.query(CourseIDMapping).filter(
            CourseIDMapping.original_id == original_course_id,
            CourseIDMapping.entity_type == 'course'
        ).first().new_id
        return course_id

    def _get_current_position(self, course_id):
        current_position = self.session_import.query(CourseLecture).filter(
            CourseLecture.course_id == course_id
        ).order_by(
            CourseLecture.position.desc()
        ).first().position
        return current_position
        
    def _get_lecture_count(self, course_id):
        # Note: For courses created with APPSMITH, getting lecture_count from COURSE will be incorrect -> need to count lectures from COURSE_LECTURE
        lecture_count = self.session_import.query(Course).filter(
            Course.id == course_id
        ).first().lecture_count
        return lecture_count

    def _get_id_mapping_list(self, original_id: int, entity_type: str) -> List[CourseIDMapping]:
        try:
            return self.session_import.query(CourseIDMapping).filter(
                CourseIDMapping.original_id == original_id,
                CourseIDMapping.entity_type == entity_type
            ).order_by(CourseIDMapping.id).all()
        except Exception as e:
            logger.error(f"Error finding id mapping list for `{entity_type}` - {original_id}: {e}")
            print(e)
            return []
        
    def _is_changed(self, updated_at: str, log: CourseIDMapping) -> bool:
        converted_updated_at = datetime.fromisoformat(updated_at.rstrip('Z')) 
        return converted_updated_at > log.created_at
    
    # def _get_current_position(self, course_id: int) -> int:
    #     return 1 + self.session_import.query(CourseLecture).filter(CourseLecture.course_id == course_id).order_by(CourseLecture.id.desc()).first().position
    
    def _update_positions(self, course_id, course_lecture_id):
        position = self.session_import.query(CourseLecture).filter(CourseLecture.id == course_lecture_id).first().position
        len_position = self.session_import.query(CourseLecture).filter(CourseLecture.course_id == course_id).count()
        if position < len_position-1:
            updated_list = self.session_import.query(CourseLecture).filter(
                CourseLecture.course_id == course_id,
                CourseLecture.position >= position
            ).order_by(
                CourseLecture.position.asc()
            ).update(
                {CourseLecture.position: CourseLecture.position + 1}, synchronize_session=False
            )
            logger.info(f"Updated positions for {len(updated_list)} lectures - course {course_id}")
        else:
            logger.info(f"No lectures to update positions - course {course_id}")
    
    def _get_content_id(self, course_lecture_id):
        lecture_id = self.session_import.query(CourseLecture).filter(CourseLecture.id == course_lecture_id).first().lecture_id
        content_id = self.session_import.query(Lecture).filter(Lecture.id == lecture_id).first().content_id
        return int(content_id)

    def _update_record(self, table_model, record_id, values):
        try:
            statement = update(table_model).where(table_model.id == record_id).values(**values)
            self.session_import.execute(statement)
            self.session_import.commit()
            logger.info(f"Record with ID {record_id} in table {table_model.__tablename__} updated successfully.")
            return True
        except Exception as e:
            logger.error(f"Error updating record {record_id} in table {table_model.__tablename__}: {e}")
            print(e)
            return False
    
    def _update_guide_videos(self, math_type_data_dict, course_id, lecture_count):
        guide_videos = math_type_data_dict.get('guide_videos')
        if guide_videos:
            for guide_video in guide_videos:
                guide_video_id = guide_video.get('id')
                id_mapping_list = self._get_id_mapping_list(guide_video_id, 'media')
                if id_mapping_list: # The guide video is already in the database
                    if self._is_changed(guide_video.get('updatedAt'), id_mapping_list[0]): # Need to update all of guide videos
                        update_mapping_list = []
                        guide_video_title = guide_video.get('title')
                        guide_video_url = guide_video.get('url')
                        for id_mapping in id_mapping_list:
                            update_mapping = {
                                'id': self._get_content_id(id_mapping.new_id),
                                'title': guide_video_title,
                                'url': guide_video_url
                            }
                            update_mapping_list.append(update_mapping)
                        self.session_import.bulk_update_mappings(Media, update_mapping_list)
                else:
                    media = self.process_media(guide_video)
                    if media:
                        self.session_import.add(media)
                        guide_video_data_dict = math_type_data_dict.copy()
                        guide_video_data_dict['title'] = 'Video'

                        lecture_math_type_media = self.processor.process_lecture(lecture_data=guide_video_data_dict, content_id=media.id, content_type='video')
                        self.session_import.add(lecture_math_type_media)


        else:
            pass # TODO: Remove imported guide videos

    def _update_chapters(self, course, course_data_dict, lecture_count, is_free, current_position):
        course_id_mapping_list = []
        chapters = course_data_dict.get('table_of_contents')
        if chapters:
            for chapter_idx, chapter_dict in enumerate(chapters):
                id_mapping_list = self._get_id_mapping_list(chapter_dict.get('id'), 'chapter')
                if id_mapping_list:
                    pass # TODO: Update chapter
                else: # Import new chapter
                    id_mapping_list, lecture_count, current_position = self._add_chapter(course, chapter_dict, lecture_count, is_free, current_position)
                    course_id_mapping_list.extend(id_mapping_list)
        return course_id_mapping_list, lecture_count, current_position
    


    def update_course(self, original_course_id: int, is_free: bool=False):
        course_id_mapping_list = []
        course_id = self._get_course_id(original_course_id)
        course = self.session_import.query(Course).filter(Course.id == course_id).first()
        current_position = self._get_current_position(course_id) + 1
        lecture_count = self._get_lecture_count(course_id)

        course_data_dict = self.processor.get_data_dict(original_course_id, 'course')

        course.updated_at = course_data_dict.get('updatedAt')
        course.title = course_data_dict.get('title')
        course.description = course_data_dict.get('description')
        # course.published_at = course_data_dict.get('publishedAt')
        course.grade_id = self.processor._get_mapped_id(course_data_dict.get('grade').get('id'), GradeIDMapping)
        course.subject_id = self.processor._get_mapped_id(course_data_dict.get('subject').get('id'), SubjectIDMapping)

        id_mapping_list, lecture_count, current_position = self._update_chapters(
            course, course_data_dict, lecture_count, is_free, current_position
        )

        course_id_mapping_list.extend(id_mapping_list)
        self.session_import.add_all(course_id_mapping_list)

        course.lecture_count = lecture_count

        self.session_import.commit()