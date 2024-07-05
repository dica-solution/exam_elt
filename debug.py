from src.database import get_session_from_engine
from src.services.cms_course_old_version_importer import CourseParser
from src.services.process_questions import QuestionProcessor
from src.config.config import get_settings
from sqlalchemy import create_engine

test_question_list = [
    {
        "id": 35,
        "label_a": "<p><span class=\"math-tex\">\\(\\left(-\\infty ; \\frac{-1}{2}\\right)\\)</span>.</p>",
        "label_b": "<p><span class=\"math-tex\">\\((0 ;+\\infty)\\)</span></p>",
        "label_c": "<p><span class=\"math-tex\">\\(\\left(\\frac{-1}{2} ;+\\infty\\right)\\)</span>.</p>",
        "label_d": "<p><span class=\"math-tex\">\\((-\\infty ; 0)\\)</span>.</p>",
        "correct_answer": "label_d",
        "explanation": "<p><span class=\"math-tex\">\\(y^{\\prime}=8 x^{3}\\lt 0 \\Leftrightarrow x\\lt 0\\)</span></p><p>Hàm số nghịch biến trên&nbsp;<span class=\"math-tex\">\\((-\\infty ; 0)\\)</span>.</p>",
        "title": "Câu 1",
        "question_content": "<p>Hàm số&nbsp;<span class=\"math-tex\">\\(y=2 x^{4}+1\\)</span>&nbsp;nghịch biến trên khoảng nào?</p>",
        "question_audio": None,
        "question_images": None,
        "question_levels": [],
        "guide_videos": None
    },
    {
        "id": 34,
        "label_a": "<p>Hàm số nghịch biến trên khoảng&nbsp;<span class=\"math-tex\">\\(\\left(\\frac{1}{3} ; 1\\right)\\)</span>.</p>",
        "label_b": "<p>Hàm số đồng biến trên khoảng&nbsp;<span class=\"math-tex\">\\(\\left(\\frac{1}{3} ; 1\\right)\\)</span>.</p>",
        "label_c": "<p>Hàm số nghịch biến trên khoảng&nbsp;<span class=\"math-tex\">\\(\\left(-\\infty ; \\frac{1}{3}\\right)\\)</span>.</p>",
        "label_d": "<p>Hàm số đồng biến trên khoảng&nbsp;<span class=\"math-tex\">\\((1 ;+\\infty)\\)</span>.</p>",
        "correct_answer": "label_a",
        "explanation": "<p><span class=\"math-tex\">\\(y^{\\prime}=3 x^{2}-4 x+1\\lt 0 \\Leftrightarrow \\frac{1}{3}\\lt x\\lt 1\\)</span></p><p>Hàm số nghịch biến trên khoảng&nbsp;<span class=\"math-tex\">\\(\\left(\\frac{1}{3} ; 1\\right)\\)</span>.</p>",
        "title": "Câu 2",
        "question_content": "<p>Cho hàm số&nbsp;<span class=\"math-tex\">\\(y=x^{3}-2 x^{2}+x+1\\)</span>. Mệnh đề nào dưới đây đúng?</p>",
        "question_audio": None,
        "question_images": None,
        "question_levels": [],
        "guide_videos": None
    }
]

def main():
    settings = get_settings()
    db_url = f"{settings.database_url}{settings.db_destination}"
    engine = create_engine(db_url)
    with get_session_from_engine(engine) as session:
        parser = CourseParser(session, settings)
        parser.import_courses()
        # question_processor = QuestionProcessor(session=session, question_list=test_question_list, question_type="quiz", quiz_collection_name="test", user_id=1, grade_id=12, subject_id=14)
        # quiz_collection_group_id = question_processor.process_questions_old_version()
        # print(quiz_collection_group_id)

if __name__ == "__main__":
    main()
    