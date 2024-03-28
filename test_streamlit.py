import streamlit as st
import json

# Set page configuration to wide mode
st.set_page_config(layout="wide")




def save_to_json(data, file_path):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file)

file_path = "test.json"
with open(file_path, "r") as json_file:
    data = json.load(json_file)


idx = st.slider('Choose index: ', 0, len(data), 1)
st.write(f'\nIndex: {idx}')
st.write(f"\nChapter: {data[idx]['chapter']}")
st.write(f"\nProblem Link: {data[idx]['url']}")
st.write(f"\nNumber of problem types: {len(data[idx]['problem_types'])}")
for step in data[idx]['problem_types']:
    st.write("\n-----------------------------------\n")
    # st.subheader(f"\n{step['problem_type']}")
    st.markdown(f"[**{step['problem_type']}**]({step['problem_link']})")
    st.write(f"\nSolution_steps:")
    st.text(f"\n{step['solution_steps']}")
    # if st.button("Is this bad solution?", key = "1"):
    #     step['bad_solution_steps'] = True
    
    # if st.button("Save", type='primary'):
    #     save_to_json(data, file_path)
    