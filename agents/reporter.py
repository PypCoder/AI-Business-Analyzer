from langchain_core.prompts import ChatPromptTemplate
from core.llm import llm

report_prompt = ChatPromptTemplate.from_template(
"""
You are a senior AI business strategist.

Your task is to generate a structured, strategic business report.

----------------------------------------
🎯 Current Goal:
{goal}

----------------------------------------
🧠 Relevant Past Insights:
(These are summaries from previous related analyses. 
Use them only if relevant. Avoid repetition.)
{past_insights}

----------------------------------------
🔎 New Research Data:
{research_data}

----------------------------------------
INSTRUCTIONS:

- Combine past insights and new research intelligently.
- Avoid repeating information already covered in past insights.
- Highlight what is NEW, UPDATED, or DIFFERENT.
- Be strategic, not generic.
- Use clear, structured sections.
- Provide actionable, realistic recommendations.

----------------------------------------
OUTPUT FORMAT:

## 1. Executive Summary

## 2. Market & Competitor Landscape

## 3. Key Opportunities

## 4. Risks & Challenges

## 5. Strategic Recommendations

## 6. 30-60-90 Day Action Plan
"""
)
report_chain = report_prompt | llm

def report_task(goal, research_data, past_insights=None):
    return report_chain.invoke({
        "goal": goal,
        "research_data": research_data,
        "past_insights": past_insights or ""
    })