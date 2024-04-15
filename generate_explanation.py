import json
import requests
import tqdm
import time
import openai
import re
import argparse
import mistune

client = openai.OpenAI(api_key="Dica-pOg5cWgMq6zgMGjR",
                base_url="https://internal-luminous.giainhanh.vn/api/v1")

system_prompt = open("src/prompts/safeguard_prompt.txt", "r").read()
user_prompt = open("src/prompts/user_prompt_multi_choise_ques_without_hint.txt", "r").read()
model = "gpt-4-0125-preview"
init_messages = [{"role": "system", "content": system_prompt}]

def get_user_prompt(question, options, correct_option, hint):
    if hint:
        user_prompt = open("src/prompts/user_prompt_multi_choise_ques_with_hint.txt", "r").read()
        user_prompt = user_prompt.replace("[question_value]", question).replace("[options_value]", options).replace("[correct_option_value]", correct_option).replace("[hint_value]", hint)
    else:
        user_prompt = open("src/prompts/user_prompt_multi_choise_ques_without_hint.txt", "r").read()
        user_prompt = user_prompt.replace("[question_value]", question).replace("[options_value]", options).replace("[correct_option_value]", correct_option)
    return user_prompt

def wrap_latex_with_span(text):
    patterns = [r'\\\((.*?)\\\)', r'\\\[(.*?)\\\]']

    for i in range(2):
        if i == 0:
            pattern = patterns[i]
            def replace_latex(match):
                return r'<span class="math-tex">\({}\)</span>'.format(match.group(1))
            text = re.sub(pattern, replace_latex, text)
        if i == 1:
            pattern = patterns[i]
            def replace_latex(match):
                return r'<span class="math-tex">\[{}\]</span>'.format(match.group(1))
            text = re.sub(pattern, replace_latex, text)
    return text

def get_explanation(prompt, model=model, init_messages=init_messages, max_retries=2):
    try:
        message = [{"role": "system", "content": system_prompt},
                              {"role": "user", "content": prompt}]
        response = client.chat.completions.create(
                    model=model,
                    messages=message,
                    temperature=0.7,
                    stream=False
                )
        explanation = response.choices[0].message.content
        html_parser = mistune.create_markdown(
            escape=False,
            plugins=['strikethrough', 'footnotes', 'table', 'speedup', 'url', 'math', 'superscript', 'subscript']
        )
        explanation = html_parser(wrap_latex_with_span(explanation))
        return explanation
    except Exception as e:
        print("Error:", e)
        return "Error"

def main():
    parser = argparse.ArgumentParser(description="Generate explanation for math questions")
    parser.add_argument('--f', type=str, help='Path to file containing math questions')
    args = parser.parse_args()

    math_filename = args.f
    # math_filename = "math_question/math_6.json"
    output_math_filename = f'{math_filename.split(".")[0]}_with_explanation.json'

    with open(math_filename, 'r') as f:
        questions = json.load(f)
    print('Total questions:', len(questions))
    questions_ = []
    for i, question in enumerate(questions):
        print(f"Processing question: {question['question_id']}, index: {i}")
        time.sleep(1)
        question_value = question['original_text']
        hint = question['original_explanation']
        options = question['quiz_options'].replace("\n", "  ")
        correct_option = question['correct_option']
        user_prompt = get_user_prompt(question_value, options, correct_option, hint)
        explanation = get_explanation(user_prompt)
        questions_.append({
            'question_id': question['question_id'],
            'mapping': question['mapping'], # 'src_exam_id', 'src_quiz_object_type', 'src_quiz_question_id', 'src_quiz_question_group_id
            'original_text': question['original_text'],
            'quiz_options': question['quiz_options'],
            'original_explanation': question['original_explanation'],
            'correct_option': question['correct_option'],
            'user_prompt': user_prompt,
            'ai_explanation': explanation,
            'version': "v1.1",
        })

        with open(output_math_filename, 'w') as f:
            json.dump(questions_, f, indent=4, ensure_ascii=False)            



if __name__ == '__main__':
    main()