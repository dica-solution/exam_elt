import streamlit as st
st.set_page_config(page_title='Grade 9 Questions', page_icon='📚', layout='wide')
import json
import re
from urllib.parse import urlencode

st.title('Review explanations for math 9 - v1.0')



def convert_latex2url(math):
    math = math.replace(r"\n", "").replace("$", "") if math.startswith("\\[") else math.replace("$", "")
    math = math[2:-2] if math.startswith("\\(") or math.startswith("\\[") else math[1:-1]
    
    params = {
    'type': 'latex',
    'from': f'''{math}'''
    }
    encoded_params = urlencode(params)
    math_converter_url = "https://math-honeycomb.giainhanh.io"
    img_url = f'{math_converter_url}/img?{encoded_params}'
    return f'![]({img_url})'

def convert_explanation(explanation):
    math_pattern = r'(\$\$|\\[\[\(])([\s\S]*?)(\$\$|\\[\]\)])'
    replaced_content = re.sub(math_pattern, lambda match: convert_latex2url(match.group(0)), explanation)

    return replaced_content


tab1, tab2, tab3, tab4 = st.tabs(["Guide", "Essay questions", "Multi-choice questions + corrected options + hints", "Multi-choice questions + corrected options"])

with tab1:
    with open('testset_essay_questions_gen_explanation.json', 'r') as f:
        questions = json.load(f)
    st.write('**Hướng dẫn**')
    st.markdown('''
    - Chọn tab `Essay questions` để xem và đánh giá giải thích AI với câu hỏi tự luận toán 9.
    - Sử dụng thanh trượt để chọn câu hỏi.
    - Với mỗi câu hỏi, hãy nhấn vào nút `Like` hoặc `Dislike` để đánh giá giải thích AI.
    - Nếu thấy hài lòng với giải thích AI - nhấn nút `Like`. Lưu ý: chỉ nên nhấn 1 lần cho một câu hỏi.  
    - Nếu thấy không hài lòng với giải thích AI - nhấn nút `Dislike`. Lưu ý: chỉ nên nhấn 1 lần cho một câu hỏi.
    - Nếu ấn nhầm `Like` trên một lần, có thể sử dụng `Dislike` giảm số lượt like xuống với số lần nhấn `Like` tương ứng.
                ''')

with tab2:

    st.write('***Với các câu hỏi tự luận toán lớp 9, có gợi ý nhưng vẫn khó hiểu. Sử dụng AI tạo giải thích dễ hiểu hơn...***')

    index = st.slider('Select question', 1, len(questions)-1, 1, step=2, key='slider1')-1

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Like', key=f'button1_{index}'):
            questions[index]['is_good_explanation'] += 1
            with open('testset_essay_questions_gen_explanation.json', 'w') as f:
                json.dump(questions, f, indent=4, ensure_ascii=False)
        if st.button('Dislike', key=f'dislike_button1_{index}'):
            questions[index]['is_good_explanation'] -= 1
            with open('testset_essay_questions_gen_explanation.json', 'w') as f:
                json.dump(questions, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index+1}:')
        st.markdown(convert_explanation(questions[index]['question_text']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header("Giải thích:")
        st.markdown(convert_explanation(questions[index]['explanation']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI giải thích:')
        st.markdown(convert_explanation(questions[index]['ai_explanation']), unsafe_allow_html=True)

    with col2:
        if st.button('Like', key=f'button2_{index}'):
            questions[index+1]['is_good_explanation'] += 1
            with open('testset_essay_questions_gen_explanation.json', 'w') as f:
                json.dump(questions, f, indent=4, ensure_ascii=False)   
        if st.button('Dislike', key=f'dislike_button2_{index}'):
            questions[index]['is_good_explanation'] -= 1
            with open('testset_essay_questions_gen_explanation.json', 'w') as f:
                json.dump(questions, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index+2}:')
        st.markdown(convert_explanation(questions[index+1]['question_text']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header("Giải thích:")
        st.markdown(convert_explanation(questions[index+1]['explanation']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI Giải thích:')
        st.markdown(convert_explanation(questions[index+1]['ai_explanation']), unsafe_allow_html=True)

with tab3:
    with open('testset_multi_choice_questions_gen_explanation.json', 'r') as f:
        questions2 = json.load(f)
    st.write('***Với các câu hỏi trắc nghiệm có đáp án và gợi ý nhưng vẫn khó hiểu, sử dụng AI để giải thích lại dễ hiểu hơn...***')
    index2 = st.slider('Select question', 1, len(questions2)-1, 1, step=2, key='slider2')-1
    col3, col4 = st.columns(2)
    with col3:
        if st.button('Like', key=f'button3_{index}'):
            questions2[index2]['is_good_explanation'] += 1
            with open('testset_multi_choice_questions_gen_explanation.json', 'w') as f:
                json.dump(questions2, f, indent=4, ensure_ascii=False)
        if st.button('Dislike', key=f'dislike_button3_{index}'):
            questions2[index2]['is_good_explanation'] -= 1
            with open('testset_multi_choice_questions_gen_explanation.json', 'w') as f:
                json.dump(questions2, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index2+1}:')
        st.markdown(convert_explanation(questions2[index2]['question_text']), unsafe_allow_html=True)
        st.markdown(convert_explanation(questions2[index2]['options']), unsafe_allow_html=True)
        st.markdown("**Đáp án đúng:**")
        st.markdown(convert_explanation(questions2[index2]['correct_option']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header("Giải thích:")
        st.markdown(convert_explanation(questions2[index2]['explanation']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI giải thích:')
        st.markdown(convert_explanation(questions2[index2]['ai_explanation']), unsafe_allow_html=True)
    with col4:
        if st.button('Like', key=f'button4_{index}'):
            questions2[index2+1]['is_good_explanation'] += 1
            with open('testset_multi_choice_questions_gen_explanation.json', 'w') as f:
                json.dump(questions2, f, indent=4, ensure_ascii=False)
        if st.button('Dislike', key=f'dislike_button4_{index}'):
            questions2[index2+1]['is_good_explanation'] -= 1
            with open('testset_multi_choice_questions_gen_explanation.json', 'w') as f:
                json.dump(questions2, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index2+2}:')
        st.markdown(convert_explanation(questions2[index2+1]['question_text']), unsafe_allow_html=True)
        st.markdown(convert_explanation(questions2[index2+1]['options']), unsafe_allow_html=True)
        st.markdown("**Đáp án đúng:**")
        st.markdown(convert_explanation(questions2[index2+1]['correct_option']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header("Giải thích:")
        st.markdown(convert_explanation(questions2[index2+1]['explanation']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI giải thích:')
        st.markdown(convert_explanation(questions2[index2+1]['ai_explanation']), unsafe_allow_html=True)

with tab4:
    st.write('***Với các câu hỏi trắc nghiệm có đáp án nhưng vẫn khó hiểu tại sao lại chọn đáp đó, sử dụng AI để tạo giải thích dễ hiểu hơn...***')
    with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'r') as f:
        questions3 = json.load(f)
    index3 = st.slider('Select question', 1, len(questions3)-1, 1, step=2, key='slider3')-1
    col5, col6 = st.columns(2)
    with col5:
        if st.button('Like', key=f'button5_{index}'):
            questions3[index3]['is_good_explanation'] += 1
            with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'w') as f:
                json.dump(questions3, f, indent=4, ensure_ascii=False)
        if st.button('Dislike', key=f'dislike_button5_{index}'):
            questions3[index3]['is_good_explanation'] -= 1
            with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'w') as f:
                json.dump(questions3, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index3+1}:')
        st.markdown(convert_explanation(questions3[index3]['question_text']), unsafe_allow_html=True)
        st.markdown(convert_explanation(questions3[index3]['options']), unsafe_allow_html=True)
        st.markdown("**Đáp án đúng:**")
        st.markdown(convert_explanation(questions3[index3]['correct_option']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI giải thích:')
        st.markdown(convert_explanation(questions3[index3]['ai_explanation']), unsafe_allow_html=True)
    with col6:
        if st.button('Like', key=f'button6_{index}'):
            questions3[index3+1]['is_good_explanation'] += 1
            with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'w') as f:
                json.dump(questions3, f, indent=4, ensure_ascii=False)
        if st.button('Dislike', key=f'dislike_button6_{index}'):
            questions3[index3+1]['is_good_explanation'] -= 1
            with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'w') as f:
                json.dump(questions3, f, indent=4, ensure_ascii=False)
        st.header(f'Câu hỏi {index3+2}:')
        st.markdown(convert_explanation(questions3[index3+1]['question_text']), unsafe_allow_html=True)
        st.markdown(convert_explanation(questions3[index3+1]['options']), unsafe_allow_html=True)
        st.markdown("**Đáp án đúng:**")
        st.markdown(convert_explanation(questions3[index3+1]['correct_option']), unsafe_allow_html=True)
        st.write("----------------------------------------")
        st.header('AI giải thích:')
        st.markdown(convert_explanation(questions3[index3+1]['ai_explanation']), unsafe_allow_html=True)