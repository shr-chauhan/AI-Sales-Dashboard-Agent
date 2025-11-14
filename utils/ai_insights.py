import os
from openai import OpenAI


MODEL = "gpt-4o-mini"  # or "gpt-realtime-mini"


def make_client(api_key: str | None = None):
    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()


def generate_sales_insights(summary_text: str, api_key: str | None = None) -> str:
    """
    Call the LLM to produce an executive summary and insights
    based on the computed aggregates.
    """
    client = make_client(api_key)

    system_prompt = (
        "You are a senior data analyst helping a business analyst understand a sales dataset. "
        "You get a numeric summary of sales, profit, categories, regions, and monthly trends. "
        "Return:\n"
        "1) A 3–5 sentence executive summary.\n"
        "2) 5–8 bullet-point insights (patterns, anomalies, segment performance, etc.).\n"
        "3) 3–5 concrete business recommendations.\n"
        "Keep the language clear and business-focused, not technical."
    )

    user_prompt = f"Here is the sales summary:\n\n{summary_text}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=900,
    )

    return response.choices[0].message.content
