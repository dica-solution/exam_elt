from sqlalchemy.exc import IntegrityError

# QuizTypeSingleChoice   = 1
# QuizTypeMultipleChoice = 2
# QuizTypeSingleEssay    = 3
# QuizTypeGroupEssay     = 4

QuizTypeSingleChoice   = 1
QuizTypeMultipleChoice = 2
QuizTypeSingleEssay    = 3
QuizTypeBlankFilling   = 5
QuizTypeSingleChoiceFromQuiz = 6



QuestionObjectType = "question"
AnswerObjectType = "answer"
TagObjectType = "tag"
UserObjectType = "user"
CollectionObjectType = "collection"
CommentObjectType = "comment"
ReportObjectType = "report"
ExamAttemptType = "exam_attempt"
ExamType = "exam"
QuizQuestionType = "quiz_question"
ExamAttemptAnswerType = "exam_attempt_answer"

ObjectTypeStrMapping = {
    QuestionObjectType: 1,
    AnswerObjectType: 2,
    TagObjectType: 3,
    UserObjectType: 4,
    CollectionObjectType: 6,
    CommentObjectType: 7,
    ReportObjectType: 8,
    ExamAttemptType: 9,
    ExamType: 10,
    QuizQuestionType: 11,
    ExamAttemptAnswerType: 12,
}

ObjectTypeNumberMapping = {
    1: QuestionObjectType,
    2: AnswerObjectType,
    3: TagObjectType,
    4: UserObjectType,
    6: CollectionObjectType,
    7: CommentObjectType,
    8: ReportObjectType,
    9: ExamAttemptType,
    10: ExamType,
    11: QuizQuestionType,
    12: ExamAttemptAnswerType,
}

def get_unique_id(store, key):
    object_type = ObjectTypeStrMapping[key]

    try:
        uqniqid = store.incr("question_bank_index")
        return f"1{object_type:03d}{uqniqid:013d}"
    except IntegrityError as _:
        raise
    except Exception as e:
        raise ValueError("get_unique_id error:  %s" % str(e))
    

GradeIDMapping = {
    # 1: 1,
    # 1: 2,
    # 1: 3,
    18: 4,
    19: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
}

SubjectIDMapping = {
    12: 1,
    44: 2,
    6: 3,
    7: 4,
    3: 5,
    # : 6,
    5: 7,
    # 1: 8,
    9: 9,
    4: 10,
    8: 11,
    45: 12,
    11: 13,
    1: 14,
    # 1: 15,
    # 1: 16,
    2: 17,
}


QuizAnswerMapping = {
    1: 'labelA',
    2: 'labelB',
    3: 'labelC',
    4: 'labelD',
}