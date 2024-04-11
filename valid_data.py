import streamlit as st
st.set_page_config(page_title='Grade 9 Questions', page_icon='📚', layout='wide')
import json
import re
from urllib.parse import urlencode

st.title('Review explanations for math 9 - v1.0')

with open('testset_essay_questions_gen_explanation.json', 'r') as f:
    questions = json.load(f)

def convert_latex2url(math):
    math = math[2:-2] if math.startswith("\\(") or math.startswith("\\[") else math[1:-1]
    math = math.replace(r"\n", "").replace("$", "")
    params = {
    'type': 'latex',
    'from': f'''{math}'''
    }
    encoded_params = urlencode(params)
    math_converter_url = "https://math-honeycomb.giainhanh.io"
    img_url = f'{math_converter_url}/img?{encoded_params}'
    return f'![]({img_url})'

def convert_explanation(explanation):
    # # Find all math expressions
    # math_expressions = re.findall(r'\$\$(.*?)\$\$|\$(.*?)\$|\\\((.*?)\\\) |\\ \[(.*?)\\\]', explanation)
    # math_regex = r'(\\\(.*?\\\)|\\\[(.*?)\\\])'
    # math_regex = r'(\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)'
    math_pattern = r'(\$\$|\\[\[\(])([\s\S]*?)(\$\$|\\[\]\)])'
    replaced_content = re.sub(math_pattern, lambda match: convert_latex2url(match.group(0)), explanation)

    return replaced_content

# result = convert_explanation(questions[2]['ai_explanation'])
# print(result)

index = st.slider('Select question', 1, len(questions)-1, 1, step=2)-1

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
