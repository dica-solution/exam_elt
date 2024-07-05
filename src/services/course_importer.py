import json
from typing import Any, Dict, List, Optional, Tuple
# from src.models.quizz_models import Course, CourseComponents, \
#     CourseGradeLinks, CourseSubjectLinks, ComponentsCourseOverviews, ComponentsCourseChapters, \
#     ComponentsCourseChaptersCourseLessonsLinks, ComponentsCourseChaptersCourseLessonsLinks, \
#     ComponentsCourseChaptersCourseLessonsLinks, CourseLessons, CourseLessonsComponents, \
#     CourseLessonsPracticesLinks, CourseLevels, CourseForms, CourseFormsComponents, \
#     CourseFormsPracticesLinks, CourseFormsExamplesLinks, CourseFormsExamplesLinks, \
#     CourseFormsComponents, QuestionGroups, QuestionGroupsComponents, ComponentsCourseExampleQuizs, \
#     ComponentsCourseExampleQuizsQuestionLevelsLinks, ComponentsCourseExampleEssays, \
#     ComponentsCourseExampleEssaysQuestionLevelsLinks, CourseLevels, ComponentsCoursePracticeEssays, \
#     ComponentsCoursePracticeEssaysQuestionLevelsLinks, ComponentsCoursePracticeQuizs, \
#     ComponentsCoursePracticeQuizsQuestionLevelsLinks
from src.models.quizz_models import *
from src.config.config import settings, Settings
from sqlalchemy.orm import Session
import requests
import re
from src.services.logger import log_runtime

class PrepCourse:
    def __init__(self):
        pass

class CourseParser:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
    
    def extract_data_dict(self, id: int, type:str, settings: Settings):
        if type == 'course':
            url = settings.api_course_detail.replace('{COURSE_ID}', str(id))
        if type == 'lecture':
            url = settings.api_lecture_detail.replace('{LECTURE_ID}', str(id))
        if type == 'type_of_maths':
            url = settings.api_type_of_maths_detail.replace('{TYPE_OF_MATHS_ID}', str(id))
        else:
            print(f'Invalid type: {type}')
            return dict()
        headers = {
            'Authorization': f'Bearer {settings.access_key}'
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('data')
        except Exception as e:
            print(e)
            return dict()
        
    def process_course(self, course_data: Dict[str, Any]):
        try:
            course = Course(
                title=course_data.get('title', ''),
                description=course_data.get('description', ''),
                slug=course_data.get('slug', ''),
                is_preview=course_data.get('is_preview', False),
                created_at=course_data.get('created_at'),
                updated_at=course_data.get('updated_at'),
                created_by_id = 1,
                updated_by_id = 1,
            )
            return course
        except Exception as e:
            print(e)
            return None
        

    def process_single_quiz_question(self, content_type: str, quiz_question_type:str, quiz_question_data: Dict[str, Any]):
        if content_type == 'examples' and quiz_question_type == 'quiz':
            quiz_question = ComponentsCourseQuizzes(
                title = quiz_question_data.get('title', ''),
                question_content = quiz_question_data.get('questionContent', ''),
                question_audio = quiz_question_data.get('questionAudio', ''),
                label_a = quiz_question_data.get('label_a', ''),
                label_b = quiz_question_data.get('label_b', ''),
                label_c = quiz_question_data.get('label_c', ''),
                label_d = quiz_question_data.get('label_d', ''),
                correct_answer = quiz_question_data.get('correctAnswer', ''),
                explanation = quiz_question_data.get('explanation', ''),
            )
        if content_type == 'examples' and quiz_question_type == 'essay':
            quiz_question = ComponentsCourseEssays(
                title = quiz_question_data.get('title', ''),
                question_content = quiz_question_data.get('questionContent', ''),
                question_audio = quiz_question_data.get('questionAudio', ''),
                answer = quiz_question_data.get('answer', ''),
                explanation = quiz_question_data.get('explanation', ''),
            )
        if content_type == 'practices' and quiz_question_type == 'quiz':
            quiz_question = ComponentsCourseQuizzes(
                title = quiz_question_data.get('title', ''),
                question_content = quiz_question_data.get('questionContent', ''),
                question_audio = quiz_question_data.get('questionAudio', ''),
                label_a = quiz_question_data.get('label_a', ''),
                label_b = quiz_question_data.get('label_b', ''),
                label_c = quiz_question_data.get('label_c', ''),
                label_d = quiz_question_data.get('label_d', ''),
                correct_answer = quiz_question_data.get('correctAnswer', ''),
                explanation = quiz_question_data.get('explanation', ''),
            )
        if content_type == 'practices' and quiz_question_type == 'essay':
            quiz_question = ComponentsCourseEssays(
                title = quiz_question_data.get('title', ''),
                question_content = quiz_question_data.get('questionContent', ''),
                question_audio = quiz_question_data.get('questionAudio', ''),
                answer = quiz_question_data.get('answer', ''),
                explanation = quiz_question_data.get('explanation', ''),
            )

        return quiz_question
        


        
    def process_question_group(self, question_group_title: str, content_type:str, question_group_type:str, question_group_data_list: List[Dict[str, Any]]):
        question_group = QuestionGroups(
            title = question_group_title,
            created_by_id = 1,
            updated_by_id = 1
        )
        self.session.add(question_group)
        self.session.flush()
        question_group_id = question_group.id

        question_list = []
        for question_group_order,question_group_item in enumerate(question_group_data_list):
            question = self.process_single_quiz_question(content_type, question_group_type, question_group_item)
            if question:
                question_list.append(question)
        self.session.add_all(question_list)
        self.session.flush()

        for question_order,question_item in enumerate(question_list):
            question_id = question_item.id
            
        




    


    def import_course(self, course_id: int):
        # Extract Course data
        course_data_dict = self.extract_data_dict(course_id, 'course', settings)
        if course_data_dict:
            course = self.process_course(course_data_dict)
            if course:
                try:
                    # Import Course
                    self.session.add(course)
                    self.session.flush()
                    course_id = course.id

                    # Import GradeLinks, SubjectLinks
                    course_grade_links = CourseGradeLinks(
                        course_id=course_id,
                        grade_id = course_data_dict.get('grade_id'),
                    )
                    course_subject_links = CourseSubjectLinks(
                        course_id=course_id,
                        subject_id = course_data_dict.get('subject_id'),
                    )
                    self.session.add(course_grade_links)
                    self.session.add(course_subject_links)

                    # Import Chapters, Lessons, Practices, Examples,...
                    for chapter_order,chapter_item in enumerate(course_data_dict.get('table_of_contents')):
                        # Import CourseChapters
                        chapter_id = chapter_item.get('id')
                        chapter_title = chapter_item.get('title')
                        chapter = ComponentsCourseChapters(
                            title = chapter_title,
                        )


                        self.session.add(chapter)
                        self.session.flush()
                        chapter_id = chapter.id

                        # Import CourseLessons
                        for lesson_order, lesson_item in enumerate(chapter_item.get('course_lessons')):
                            lesson_id = lesson_item.get('id')
                            lesson_data_dict = self.extract_data_dict(lesson_id, 'lecture', settings)
                            if lesson_data_dict:
                                lesson = CourseLessons(
                                    title = lesson_data_dict.get('title'),
                                    slug = lesson_data_dict.get('slug'),
                                    created_at = lesson_data_dict.get('created_at'),
                                    updated_at = lesson_data_dict.get('updated_at'),
                                    published_at = lesson_data_dict.get('published_at'),
                                    created_by_id = 1,
                                    updated_by_id = 1,
                                )
                                self.session.add(lesson)
                                self.session.flush()
                                lesson_id = lesson.id

                                # Import ComponentsCourseChaptersCourseLessonsLinks
                                components_course_chapters_course_lessons_links = ComponentsCourseChaptersCourseLessonsLinks(
                                    chapter_id = chapter_id,
                                    course_lesson_id = lesson_id,
                                    course_lesson_order = lesson_order + 1
                                )
                                self.session.add(components_course_chapters_course_lessons_links)

                                for content_types_order,content_types_item in enumerate(lesson_data_dict.get('content_types')):
                                    if content_types_item.get('__component') == 'course.overview':
                                        # Import CourseOverviews
                                        overview = ComponentsCourseOverviews(
                                            title = content_types_item.get('title'),
                                            content = content_types_item.get('content'),
                                        )
                                        self.session.add(overview)
                                        self.session.flush()
                                        overview_id = overview.id

                                        # Import CourseLessonsComponents
                                        course_lessons_components = CourseLessonsComponents(
                                            entity_id = lesson_id,
                                            component_id = overview_id,
                                            component_type = 'course.overview',
                                            field = 'content_types',
                                            order = content_types_order + 1
                                        )
                                        self.session.add(course_lessons_components)
                                    if content_types_item.get('__component') == 'course.form':
                                        pass
                                        # Import CourseForms
                                        # for form_order,form_item in enumerate(content_types_item.get('course.form')):
                                        #     form_id = form_item.get('id')
                                        #     form_data_dict = self.extract_data_dict(form_id, 'type_of_maths', settings)
                                        #     if form_data_dict:
                                    if content_types_item.get('__component') == 'course.quiz':
                                        quiz_question = ComponentsCourseQuizzes(
                                            title = content_types_item.get('title'),
                                            question_content = content_types_item.get('question_content'),
                                            question_audio = content_types_item.get('question_audio'),
                                            label_a = content_types_item.get('label_a'),
                                            label_b = content_types_item.get('label_b'),
                                            label_c = content_types_item.get('label_c'),
                                            label_d = content_types_item.get('label_d'),
                                            correct_answer = content_types_item.get('correct_answer'),
                                            explanation = content_types_item.get('explanation'),
                                        )
                                        self.session.add(quiz_question)
                                        self.session.flush()
                                        quiz_question_id = quiz_question.id

                                        # Import ComponentsCourseQuizzesQuestionLevelsLinks
                                        quiz_question_levels_id = content_types_item.get('question_levels')[0].get('id')
                                        quiz_question_levels_links = ComponentsCourseQuizzesQuestionLevelsLinks(
                                            quiz_id = quiz_question_id,
                                            course_level_id = quiz_question_levels_id,
                                            course_level_order = 0
                                        )
                                        self.session.add(quiz_question_levels_links)

                                    if content_types_item.get('__component') == 'course.essay':
                                        essay_question = ComponentsCourseEssays(
                                            title = content_types_item.get('title'),
                                            question_content = content_types_item.get('question_content'),
                                            question_audio = content_types_item.get('question_audio'),
                                            answer = content_types_item.get('answer'),
                                            explanation = content_types_item.get('explanation'),
                                        )
                                        self.session.add(essay_question)
                                        self.session.flush()
                                        essay_question_id = essay_question.id

                                        # Import ComponentsCourseEssaysQuestionLevelsLinks
                                        essay_question_levels_id = content_types_item.get('question_levels')[0].get('id')
                                        essay_question_levels_links = ComponentsCourseEssaysQuestionLevelsLinks(
                                            essay_id = essay_question_id,
                                            course_level_id = essay_question_levels_id,
                                            course_level_order = 0
                                        )
                                        self.session.add(essay_question_levels_links)
                                    
                                    if content_types_item.get('__component') in ['course.group-quiz', 'course.group-essay']:
                                        if content_types_item.get('__component') == 'course.group-quiz':
                                            question_data_list = content_types_item.get('course.group-quiz')
                                        if content_types_item.get('__component') == 'course.group-essay':
                                            question_data_list = content_types_item.get('course.group-essay')
                                        

                                    
                                        
                                        




                except Exception as e:
                    print(e)
                    self.session.rollback()
                

                