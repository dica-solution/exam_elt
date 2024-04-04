from src.config.config import settings
import asyncio
import aiohttp
import json
from tqdm import tqdm

async def extract_data(session, url, headers):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
    return dict()
async def check_structured(exam_id, data):
    related_items = data.get('data').get('relatedItems')
    if len(related_items) != 5:
        return exam_id, False

    if any(item.get('__component') != 'exam.single-essay' for item in related_items[0:3]):
        return exam_id, False
    if related_items[3].get('__component') != 'exam.grouped-essay' or len(related_items[3].get('relatedEssays')) != 3:
        return exam_id, False

    if related_items[4].get('__component') != 'exam.single-essay':
        return exam_id, False


    return exam_id, True

async def main():

    lst_structured_exam_id = []

    auth_token = settings.api_authentication_token
    url = settings.api_get_by_exam_id
    headers = {'Authorization': f'Bearer {auth_token}'}

    async with aiohttp.ClientSession() as session:
        with open('id_lst.txt', 'r') as f:
            exam_ids = f.read().splitlines()
        for exam_id in tqdm(exam_ids, desc="Processing exams"):
            url = settings.api_get_by_exam_id.format(EXAM_ID=int(exam_id))
            response = await extract_data(session, url, headers)
            _, check_result = await check_structured(exam_id, response)
            if check_result:             
                lst_structured_exam_id.append(exam_id)
        with open('structured_exam_id.txt', 'w') as f:
            f.write('\n'.join(lst_structured_exam_id))

if __name__ == '__main__':
    asyncio.run(main())