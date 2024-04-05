import streamlit as st
st.set_page_config(layout='wide', page_title='Math AI Tutor 🤖', page_icon="🤖")
import requests
import json
# st.session_state.clear()
st.title("Luminous AI Chatbot")
col1, col2= st.columns(2)
def send_message(message):
    headers = { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer Dica-pOg5cWgMq6zgMGjR'
    }
    data = {
        "model": st.session_state["model"],
        "messages": st.session_state["messages"] + [{"role": "user", "content": message}],
        "temperature": 0.7,
        "stream": True
    }
    response = requests.post('https://internal-luminous.giainhanh.vn/api/v1/chat/completions', headers=headers, data=json.dumps(data), stream=True)
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                try:
                    yield json.loads(line.decode().replace('data: ', ''))['choices'][0]['delta'].get('content', '')
                except:
                    pass

with col1:
    model_name = st.selectbox(
        "Select a model",
        [
            "luminous-the-0.0",
            "gpt-4-0125-preview",
            "luminous-gep-1.0",
            "gpt-3.5-turbo",
            "luminous-gep-1.5"
        ],
        index=0,
    )

    if "model" not in st.session_state:
        st.session_state["model"] = model_name


    if "messages" not in st.session_state:
        st.session_state['messages'] = []


    for message in st.session_state.messages:
        # if message.get["role"] == "user":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if not st.session_state.messages:
        st.session_state.messages.append({"role": "system",
                                    # "content": "Giải chi tiết và dễ hiểu hoàn toàn bằng tiếng Việt. Chú ý quy đồng mẫu số. Tiếp tục cho tới khi nào tìm ra được đáp án. Không được hỏi lại bất kỳ câu nào."
                                    "content": open("src/prompts/thetawise_prompt.txt", "r").read()})
    # Accept user input
    if prompt := st.chat_input("what is your math question?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
                stream = send_message(prompt)
                response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
    if st.button('Clear Conversation'):
        st.session_state.messages = st.session_state.messages[0]

with col2:
    st.json(st.session_state, expanded=True) 