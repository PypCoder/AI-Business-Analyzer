from langchain_core.prompts import ChatPromptTemplate
from core.llm import llm

summary_prompt = ChatPromptTemplate.from_template(
"""
You are a professional summarization engine.

Summarize the following text clearly and concisely.

Text:
{text}

Return only the summary.
"""
)

summary_chain = summary_prompt | llm


def summarize_task(text: str):
    return summary_chain.invoke({"text": text})