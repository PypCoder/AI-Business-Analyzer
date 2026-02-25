from langchain_core.prompts import ChatPromptTemplate
from core.llm import llm

planner_prompt = ChatPromptTemplate.from_template(
"""
You are an AI planning module.

Break the user's goal into 5 short, web-searchable queries.

Goal: {goal}

Return each query on a new line, max 12 words each, plain text only.
"""
)
planner_chain = planner_prompt | llm

def planner_task(goal):
    return planner_chain.invoke({"goal": goal})