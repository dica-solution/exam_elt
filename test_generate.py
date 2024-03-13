from src.config.config import settings
from src.services.generate_explanation import generate_explanation
import asyncio
import json
import time

limit_question_to_generate_explanation = 1
question_with_explantion_filename = "question_with_explantion.json"
question_empty_explantion_filename = "question_empty_explanation.json"
prompt_filename = "src/prompts/prompt.txt"
records_empty_explanation = []
records_explanation = []

with open(prompt_filename, 'r') as f:
    persona_n_prompt = f.read()

with open(question_empty_explantion_filename, 'r') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['explanation'] == '':
            records_empty_explanation.append(record)

def save_to_jsonl(data, filename):
    with open(filename, 'w') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

def append_to_jsonl(data, filename):
    with open(filename, 'a') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

print(f'Number of objects to generate explanation: {len(records_empty_explanation)}')
print(f'Limit of number question to generate explanation: {limit_question_to_generate_explanation}')

for i in range(limit_question_to_generate_explanation):
    start_time = time.time()
    try:
        explanation = asyncio.run(generate_explanation(records_empty_explanation[i]['question'], persona_n_prompt=persona_n_prompt))
        if explanation != '':
            print(f'Generate successful explanation for question {i} in {time.time() - start_time:.4f}s')
            del records_empty_explanation[i]

    except Exception as e:
        print(e)
    
    if explanation and explanation != '':
        records_empty_explanation[i]['explanation'] = explanation
        records_explanation.append(records_empty_explanation[i])


save_to_jsonl(records_empty_explanation, question_empty_explantion_filename)
append_to_jsonl(records_explanation, question_with_explantion_filename)