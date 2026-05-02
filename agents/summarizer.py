from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm

llm = get_llm()

summary_prompt = ChatPromptTemplate.from_template(
"""
You are a professional summarization engine.

Summarize the following text clearly and concisely.

Text:
{text}

Return only the summary.
"""
)

def summarize_task(text: str):
    summary_chain = summary_prompt | llm
    return summary_chain.invoke({"text": text})