import requests
from bs4 import BeautifulSoup
import time
import json

# URL to crawl
# url = "https://vietjack.com/toan-lop-6/index.jsp"
chapters = [
    {"chapter": "Tập hợp các số tự nhiên", "url": "https://vietjack.com/toan-lop-6/chuong-1-tap-hop-cac-so-tu-nhien-sm.jsp"},
    {"chapter": "Tính chia hết trong tập hợp các số tự nhiên", "url": "https://vietjack.com/toan-lop-6/chuong-2-tinh-chia-het-trong-tap-hop-cac-so-tu-nhien-sm.jsp"},
    {"chapter": "Số nguyên", "url": "https://vietjack.com/toan-lop-6/chuong-3-so-nguyen-sm.jsp"},
    {"chapter": "Một số hình phẳng trong thực tiễn", "url": "https://vietjack.com/toan-lop-6/chuong-4-mot-so-hinh-phang-trong-thuc-tien-sm.jsp"},
    {"chapter": "Một số yếu tố thống kê", "url": "https://vietjack.com/toan-lop-6/chuong-4-mot-so-yeu-to-thong-ke-sm.jsp"},
    {"chapter": "Tính đối xứng của hình phẳng trong tự nhiên", "url": "https://vietjack.com/toan-lop-6/chuong-5-tinh-doi-xung-cua-hinh-phang-trong-tu-nhien-sm.jsp"},
    {"chapter": "Phân số", "url": "https://vietjack.com/toan-lop-6/chuong-6-phan-so-sm.jsp"},
    {"chapter": "Số thập phân", "url": "https://vietjack.com/toan-lop-6/chuong-7-so-thap-phan-sm.jsp"},
    {"chapter": "Những hình học cơ bản", "url": "https://vietjack.com/toan-lop-6/chuong-8-nhung-hinh-hoc-co-ban-sm.jsp"},
    {"chapter": "Dữ liệu và xác suất thực nghiệm", "url": "https://vietjack.com/toan-lop-6/chuong-9-du-lieu-va-xac-suat-thuc-nghiem-sm.jsp"}
]

def get_solution_steps(url):
    time.sleep(1)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    solution_steps = ""

    phana_anchor = soup.find('a', {'name': 'phana'})
    phanb_anchor = soup.find('a', {'name': 'phanb'})
    phan1a_anchor = soup.find('a', {'name': 'phan1a'})
    phan1b_anchor = soup.find('a', {'name': 'phan1b'})
    if phana_anchor and phanb_anchor:
        current_tag = phana_anchor.find_next_sibling()
        while current_tag and current_tag != phanb_anchor:
            if current_tag.name == 'p' and not current_tag.find('strong'):
                solution_steps += ('\n'+current_tag.text)
            current_tag = current_tag.find_next_sibling()
    elif phan1a_anchor and phan1b_anchor:
        current_tag = phan1a_anchor.find_next_sibling()
        while current_tag and current_tag != phan1b_anchor:
            if current_tag.name == 'p' and not current_tag.find('strong'):
                solution_steps += ('\n'+current_tag.text)
            current_tag = current_tag.find_next_sibling()
    else:
        print(f"One or both of the anchor tags not found. | {url}")

    return solution_steps


# Get list of links
for chapter in chapters:
    response = requests.get(chapter.get('url'))
    soup = BeautifulSoup(response.text, "html.parser")
    lst = soup.find_all('ul', class_='list')[0].find_all('li')
    chapter['problem_types'] = []
    for item in lst:
        problem_type = item.text
        problem_link = item.find('a')['href'].replace("..", "https://vietjack.com")
        chapter['problem_types'].append({"problem_type": problem_type.strip(), "problem_link": problem_link, "solution_steps": get_solution_steps(problem_link)})
        
with open("test.json", "w") as json_file:
    json.dump(chapters, json_file, ensure_ascii=False, indent=4)

print('hello world!')