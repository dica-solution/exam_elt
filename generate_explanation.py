import json
import requests
import tqdm
import time
import openai

client = openai.OpenAI(api_key="Dica-pOg5cWgMq6zgMGjR",
                base_url="https://internal-luminous.giainhanh.vn/api/v1")

system_prompt = open("src/prompts/safeguard_prompt.txt", "r").read()
user_prompt = open("src/prompts/user_prompt_multi_choise_ques_without_hint.txt", "r").read()
model = "gpt-4-0125-preview"
init_messages = [{"role": "system", "content": system_prompt}]

def get_user_prompt(question_value, options, correct_option, user_prompt=user_prompt):
    user_prompt = user_prompt.replace("[question_value]", question_value).replace("[options_value]", options).replace("[correct_option_value]", correct_option)
    return user_prompt

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
        return explanation
    except Exception as e:
        print("Error:", e)
        return "Error"

def main():
    with open('testset_multi_choice_questions.json', 'r') as f:
        questions = json.load(f)
    print('Total questions:', len(questions))
    questions_ = []
    for i, question in enumerate(questions):
        print(f"Processing question: {question['question_id']}, index: {i}")
        time.sleep(1)
        question_value = question['question_text']
        # hint_value = question['explanation']
        options = question['options'].replace("\n", "  ")
        correct_option = question['correct_option']
        user_prompt = get_user_prompt(question_value, options, correct_option)
        explanation = get_explanation(user_prompt)
        questions_.append({
            'question_id': question['question_id'],
            'question_text': question['question_text'],
            'options': question['options'],
            # 'explanation': question['explanation'],
            'correct_option': question['correct_option'],
            'user_prompt': user_prompt,
            'ai_explanation': explanation,
            'version': "v1.1",
            "is_good_explanation": 0
        })

        with open('testset_multi_choice_questions_without_hint_gen_explanation.json', 'w') as f:
            json.dump(questions_, f, indent=4, ensure_ascii=False)            
    #     # print(explanation)


if __name__ == '__main__':
    main()