import zipfile
import lxml.etree as ET
import json
import base64
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
    doc_path = r'C:\Users\ys770\PycharmProjects\resume\chatbot-tester\backend\jobhireai-resume-templates\templates\Modern Resume.docx'

    # Extract original text nodes
    with zipfile.ZipFile(doc_path, 'r') as zf:
        xml_content = zf.read('word/document.xml')
        
    tree = ET.fromstring(xml_content)
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text_elements = tree.xpath('//w:t', namespaces=namespaces)

    original_strings = {}
    for idx, t in enumerate(text_elements):
        if t.text:
            original_strings[str(idx)] = t.text

    # Prompt AI
    llm = ChatOpenAI(
        model='stepfun/step-3.5-flash:free',
        openai_api_key=os.environ.get('OPENROUTER_API_KEY'),
        openai_api_base='https://openrouter.ai/api/v1',
        max_tokens=2500,
    )
    
    sys_prompt = '''You are a strict data-replacement bot. The user will give you two things:
1. "Profile Data": A JSON of a real person's scraped profile.
2. "Template Text map": A JSON dictionary { "id": "original sample formatting string" } extracted from a mock Resume Document.

Your task is to replace the mock data with the real "Profile Data".
Return ONLY a valid JSON dictionary { "id": "new string" } covering ALL the same IDs provided.
- Ensure split strings match context (e.g. if id 0 is "John ", and id 1 is "Doe", map id 0 to real first name and id 1 to real last name).
- If an original string is punctuation, a star, or just whitespace, leave it exactly as-is.
- If it's a placeholder header like "Education", keep it "Education".
- Return ONLY the raw JSON string. Do not wrap in markdown boxes.'''
    
    usr_prompt = "Profile Data: {'name': 'Linus Torvalds', 'headline': 'Linux Creator'}\n\nTemplate Text map:\n" + json.dumps(original_strings)
    
    resp = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=usr_prompt)])
    res_str = resp.content.strip()
    if res_str.startswith('```json'):
        res_str = res_str[7:]
    if res_str.endswith('```'):
        res_str = res_str[:-3]
    
    replacements = json.loads(res_str.strip())
    
    # Apply replacements
    for idx, t in enumerate(text_elements):
        if str(idx) in replacements:
            t.text = replacements[str(idx)]
            
    # Save a new zip docx
    new_xml_content = ET.tostring(tree, encoding='unicode')
    
    with zipfile.ZipFile(doc_path, 'r') as zin:
        with zipfile.ZipFile('test_output.docx', 'w') as zout:
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item, new_xml_content)
                else:
                    zout.writestr(item, zin.read(item.filename))
                    
    print("SAVED test_output.docx! Success")
except Exception as e:
    import traceback
    traceback.print_exc()
