import json
import requests
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load .env file if it exists
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(dotenv_path):
    with open(dotenv_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

try:
    llm = ChatOpenAI(
        model='stepfun/step-3.5-flash:free',
        openai_api_key=os.environ.get('OPENROUTER_API_KEY'),
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
