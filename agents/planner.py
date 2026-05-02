from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm

llm = get_llm()

planner_prompt = ChatPromptTemplate.from_template(
"""
You are an AI planning module.

Break the user's goal into 5 short, web-searchable queries.

Goal: {goal}

Return each query on a new line, max 12 words each, plain text only.
"""
)

def planner_task(goal):
    planner_chain = planner_prompt | llm
    return planner_chain.invoke({"goal": goal})