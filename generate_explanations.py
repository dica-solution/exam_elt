import time
import json
import asyncio
import aiohttp

async def get_explanation(session, url, headers, text):
    data = {'text': text+"\n Giải chi tiết từng bước. Không được đưa ra câu hỏi gợi ý."}
    async with session.post(url, headers=headers, data=json.dumps(data)) as response:
        return await response.json()
    
async def main():
    url = 'http://dev-database:18003/api/v1/answer/answer-text'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer Dica-pOg5cWgMq6zgMGjR'
    }
    async with aiohttp.ClientSession() as session:
        with open('grade_6_questions.json', 'r') as f:
            questions = json.load(f)
        for question in questions:
            explanation = await get_explanation(session, url, headers, question['question_text'])
            question['explanation_by_ai'] = explanation['text']
            # print(question)
        with open('grade_6_questions_with_explanation.json', 'w') as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)

    print("Done")
if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    print(f"Time taken: {time.time() - start_time}")