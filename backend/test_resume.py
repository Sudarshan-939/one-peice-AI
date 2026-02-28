import json
import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

try:
    llm = ChatOpenAI(
        model='stepfun/step-3.5-flash:free',
        openai_api_key='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',
        openai_api_base='https://openrouter.ai/api/v1',
        max_tokens=2500,
    )
    sys_prompt = '''You are an expert web developer and resume designer. 
    Your task is to generate a complete, valid HTML file containing a stunning, responsive, minimalist resume based ONLY on the provided JSON profile data.
    Follow the Simple Resume Two-column HTML, CSS style design aesthetic. Include embedded CSS within a <style> tag in the <head>. Do NOT use external CSS files except for fonts or icons (like FontAwesome or Google Fonts).
    Make sure the design is professional, uses modern typography (e.g. Inter or Roboto), subtle shadows, and a clean layout.
    IMPORTANT: Return ONLY raw HTML code. Do NOT wrap the HTML in markdown blocks like ```html. Start exactly with <!DOCTYPE html> and end with </html>.'''

    user_prompt = "Here is the scraped profile data: {'name': 'John Doe'}"

    resp = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
    print("RESPONSE:", repr(resp.content))
except Exception as e:
    print("ERROR:", e)
