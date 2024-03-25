import os
import asyncio
from sydney import SydneyClient


os.environ["BING_COOKIES"] = open('src/prompts/copilot_cookies.txt', 'r').read()

async def generate_explanation(question: str, persona_n_prompt:str) -> None:
    question = f"If your response meet Latex, you wrap it in span tag and 'math-tex' class.\n{question}"
    async with SydneyClient(style='precise') as sydney:
        
        for i in range(4): # Retry 4 times
            await sydney.reset_conversation()
            response = await sydney.ask(question, context=persona_n_prompt)
            if response:
                return response
                break
        return ""


# if __name__ == "__main__":
    # prompt = "who are you?"
    # prompt = "<p>Tiệm bánh sinh nhật Lisa bán hai loại bánh: bánh mặn và bánh ngọt. Mỗi ngày, tiệm này luôn trưng bày tổng cộng không quá 20 cái bánh gồm cả bánh mặn và bánh ngọt. Hơn nữa, số bánh mặn được trưng bày luôn ít hơn 8. Gọi x, y lần lượt là số bánh mặn và bánh ngọt được trưng bày mỗi ngày. Hãy lập hệ bất phương trình mô tả điều kiện của x y, và biểu diễn miền nghiệm của hệ bất phương đó trên hệ trục toạ độ Oxy .</p>"
    # asyncio.run(generate_explanation(prompt))