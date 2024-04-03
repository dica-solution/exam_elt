import streamlit as st
import json

st.set_page_config(page_title='Grade 6 Questions', page_icon='📚', layout='wide')

with open('grade_6_questions_with_explanation.json', 'r') as f:
    questions = json.load(f)

index = st.slider('Select question', 0, len(questions)-1, 0)

# Display the question ID
st.write(questions[index]['question_id'])

# Display the question text
st.markdown('**Question:**')
st.text(questions[index]['question_text'])

# Display the correct option
st.markdown('**Correct Option:**')
st.text(questions[index]['correct_option'])

# Display the explanation
st.markdown('**Explanation:**')
st.text(questions[index]['explanation'])

# Display the AI explanation
st.markdown('**AI Explanation:**')
st.text(questions[index]['explanation_by_ai'])

if st.button('Good Explanation'):
    questions[index]['good_explanation'] = True
    with open('grade_6_questions_with_explanation.json', 'w') as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
    st.write('Marked as a good explanation')

# message = "My ability to assist with math problems stems from a few key features and processes:\n\n1. **Mathematical Knowledge Base**: I'm programmed with a solid foundation in mathematical concepts, theories, and problem-solving strategies that span various topics, from basic arithmetic to advanced calculus and linear algebra.\n\n2. **SymPy Integration**: For many mathematical operations, especially those involving calculus and algebra, I use SymPy, a Python library for symbolic mathematics. This allows me to generate detailed solutions for integrals, derivatives, equations, and more.\n\n3. **Plotting Capabilities**: When visual understanding of a problem is crucial, I can generate plots for functions. This is particularly helpful for understanding the behavior of functions, solving graph-related problems, or illustrating concepts like limits and continuity.\n\n4. **Step-by-Step Explanations**: I can provide detailed, step-by-step explanations for a wide range of mathematical problems. This not only includes the final answer but also the reasoning and intermediate steps to reach that answer, which is critical for learning.\n\n5. **Adaptability to User Queries**: I'm designed to understand and adapt to the user's query, whether it's solving an equation, proving a theorem, or explaining a concept. This involves parsing the mathematical notation and intent behind the question.\n\n6. **Error Checking and Clarification Requests**: If a question is unclear or incomplete, I can ask for clarifications or additional information. This helps in providing a more accurate and relevant response.\n\n7. **Use of Examples**: When explaining concepts, I often use examples to illustrate points. This helps in making abstract or complex ideas more tangible and easier to understand.\n\n8. **Interactive Learning Support**: By engaging in a back-and-forth dialogue, I can adapt explanations based on the user's understanding, ask and answer questions, and guide the learning process more effectively.\n\nThese features enable me to assist users in learning and solving a wide range of mathematical problems effectively."
# # st.markdown(message)

# mes2 = "My workflow for solving math problems involves several key steps, each designed to ensure accuracy, clarity, and understanding. Here's a breakdown of those steps:\n\n1. **Understanding the Problem:**\n   - I begin by carefully reading the question to understand exactly what is being asked. This involves identifying the main concepts, the type of math problem (e.g., algebra, calculus), and any specific requirements or constraints.\n\n2. **Identifying Relevant Information:**\n   - Next, I identify the given information and what needs to be found. This can include numbers, formulas, diagrams, or any other provided data.\n\n3. **Formulating a Strategy:**\n   - With a clear understanding of the problem, I develop a strategy for solving it. This might involve choosing appropriate formulas, deciding on a method for solving equations, or determining a step-by-step approach for complex problems.\n\n4. **Execution:**\n   - I then apply the chosen strategy to solve the problem. This can involve calculations, algebraic manipulations, applying theorems, or drawing diagrams. I perform these steps methodically to ensure accuracy.\n\n5. **Verification:**\n   - After obtaining a solution, I verify its correctness. This can involve checking calculations, ensuring the solution meets any given constraints, and confirming that it logically answers the question posed.\n\n6. **Explanation:**\n   - I provide a clear explanation of the steps taken and the reasoning behind them. This is crucial for teaching purposes and to ensure the student understands the process, not just the final answer.\n\n7. **Feedback Loop:**\n   - I ask for feedback to ensure the student has understood the explanation and to clarify any doubts. This step is essential for interactive learning and helps students become more proficient at solving similar problems in the future.\n\n8. **Use of Tools:**\n   - When necessary, I utilize various tools available within the Thetawise platform, such as equation solvers, graph plotting, or step-by-step solution generators. These tools help in providing a more comprehensive understanding and visualization of the problem and its solution.\n\n9. **Continuous Learning:**\n   - I stay updated with mathematical concepts, problem-solving techniques, and educational strategies. This ensures I can provide the most effective assistance.\n\nEach of these steps contributes to a thorough and methodical approach to solving math problems, ensuring that solutions are not only accurate but also well-understood by the student."
# st.markdown(mes2)