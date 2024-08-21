from src.models.exam_bank_models import *
from src.database import get_session_from_engine
from src.config.config import get_settings
from sqlalchemy import update, and_, create_engine
class Update():
    def __init__(self, session):
        self.session = session

    def _get_max_level(self, course_id):
        course_lecture_list = self.session.query(CourseLecture).join(
            Course, Course.id == CourseLecture.course_id
        ).filter(Course.id == course_id).all()
        max_level = max([course_lecture.level for course_lecture in course_lecture_list])
        if max_level is None:
            return 0
        return max_level
    
    def _split_courses_and_lectures(self):
        courses = self.session.query(Course).join(
            CourseLecture, Course.id == CourseLecture.course_id
        ).filter(Course.category_id == 1).all()

        lectures = self.session.query(Course).join(
            CourseLecture, Course.id == CourseLecture.course_id
        ).filter(Course.category_id == 2).all()

        return courses, lectures
    
    def _update_node_type_default(self):
        self.session.query(CourseLecture).update(
            {'node_type': 1}, synchronize_session=False
        )

        self.session.commit()

    def _update_node_type_for_courses(self, courses):
        for course in courses:
            course_id = course.id
            max_level = self._get_max_level(course_id)
            if max_level == 4:
                self.session.query(CourseLecture).filter(
                    CourseLecture.course_id == course_id
                ).filter(CourseLecture.level == max_level).update(
                    {'node_type': 2}, synchronize_session=False
                )
    def _update_node_type_for_lectures(self, lectures):
        for lecture in lectures:
            course_id = lecture.id
            max_level = self._get_max_level(course_id)
            if max_level == 2 or max_level == 3:
                self.session.query(CourseLecture).filter(
                    CourseLecture.course_id == course_id
                ).filter(CourseLecture.level == max_level).update(
                    {'node_type': 2}, synchronize_session=False
                )
    
    def update_node_type(self):
        courses, lectures = self._split_courses_and_lectures()
        self._update_node_type_default()
        self._update_node_type_for_courses(courses)
        self._update_node_type_for_lectures(lectures)
        self.session.commit()


def main():
    settings = get_settings()
    db_url = f"{settings.database_url}{settings.db_destination}"
    engine = create_engine(db_url)
    with get_session_from_engine(engine) as session:
        updater = Update(session)
        updater.update_node_type()

if __name__ == '__main__':
    main()

