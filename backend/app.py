from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
from bs4 import BeautifulSoup
from linkedin_api import Linkedin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions
import tempfile
import os
import zipfile
import base64
import lxml.etree as ET
import json

# LangChain Imports for the API proxy
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

app = Flask(__name__)
CORS(app)  # Allow CORS for the frontend to hit these APIs

# Chatbot Tester OpenRouter LangChain Proxy
MODEL_MAPPING = {
    "liquid/lfm-2.5-1.2b-instruct:free": "liquid/lfm-2.5-1.2b-instruct:free", # For backwards compat if needed
    "ramudu": "liquid/lfm-2.5-1.2b-instruct:free",
    "bemudu": "arcee-ai/trinity-large-preview:free",
    "surudu": "stepfun/step-3.5-flash:free",
}

@app.route('/api/generate_resume', methods=['POST'])
def generate_resume():
    data = request.json
    profile_data = data.get('profile_data', {})
    model_alias = data.get('model', 'surudu')  # Use surudu for coding tasks by default
    template_style = data.get('template_style', 'Simple Resume Two-column HTML, CSS')
    
    actual_model = MODEL_MAPPING.get(model_alias, "stepfun/step-3.5-flash:free")
    OPENROUTER_API_KEY = "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"
    
    try:
        llm = ChatOpenAI(
            model=actual_model,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=2500,
        )
        
        system_prompt = f"""You are an expert web developer and resume designer. 
Your task is to generate a complete, valid HTML file containing a stunning, responsive, minimalist resume based ONLY on the provided JSON profile data.
Follow the {template_style} style design aesthetic. Include embedded CSS within a <style> tag in the <head>. Do NOT use external CSS files except for fonts or icons (like FontAwesome or Google Fonts).
Make sure the design is professional, uses modern typography (e.g. Inter or Roboto), subtle shadows, and a clean layout.
IMPORTANT: Return ONLY raw HTML code. Do NOT wrap the HTML in markdown blocks like ```html. Start exactly with <!DOCTYPE html> and end with </html>."""

        user_prompt = f"Here is the scraped profile data to convert into a resume:\n{json.dumps(profile_data, indent=2)}\n\nPlease ensure it looks like a high-quality professional CV with sections for Profile, Skills, Projects/Experience, etc. as appropriate based on the data."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        
        import re
        html_content = response.content.strip()
        
        # Safely remove markdown formatting
        html_content = re.sub(r"^```(?:html)?\s*", "", html_content, flags=re.IGNORECASE)
        html_content = re.sub(r"\s*```$", "", html_content)
        
        html_content = html_content.strip()
        
        print(f"Generated HTML Resume length: {len(html_content)} chars")
            
        return jsonify({
            "status": "success",
            "html": html_content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    """Generates a real Native PDF string from raw HTML via Selenium headless Chrome"""
    data = request.json
    html_content = data.get('html_content', '')
    
    if not html_content:
        return jsonify({"error": "No HTML content provided"}), 400
        
    try:
        # 1. Write HTML to temporary file safely
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
            
        # 2. Setup Headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # 3. Load temp file into browser
        driver.get("file:///" + temp_path.replace("\\", "/"))
        time.sleep(1) # short wait for fonts/styles to flush
        
        # 4. Print native PDF!
        print_options = PrintOptions()
        print_options.background = True # Include background colors
        base64_pdf = driver.print_page(print_options)
        
        # 5. Cleanup memory
        driver.quit()
        os.remove(temp_path)
        
        return jsonify({
            "status": "success",
            "pdf_base64": base64_pdf
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_docx', methods=['POST'])
def generate_docx():
    """Generates a DOCX file directly by replacing JobHire text with user data using AI"""
    data = request.json
    profile_data = data.get('profile_data', {})
    template_style = data.get('template_style', 'Modern Resume.docx')
    model_alias = data.get('model', 'surudu')
    
    # Map alias to openrouter model
    model_mapping = {
        'ramudu': 'liquid/lfm-2.5-1.2b-instruct:free',
        'bemudu': 'arcee-ai/trinity-large-preview:free',
        'surudu': 'stepfun/step-3.5-flash:free'
    }
    model_id = model_mapping.get(model_alias, 'stepfun/step-3.5-flash:free')
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(cwd, 'jobhireai-resume-templates', 'templates', template_style)
    
    if not os.path.exists(doc_path):
        return jsonify({"error": f"Template {template_style} not found on server."}), 404
        
    try:
        # Extract original text from the template's XML
        with zipfile.ZipFile(doc_path, 'r') as zf:
            xml_content = zf.read('word/document.xml')
            
        tree = ET.fromstring(xml_content)
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text_elements = tree.xpath('//w:t', namespaces=namespaces)

        original_strings = {}
        for idx, t in enumerate(text_elements):
            if t.text and len(t.text.strip()) > 0: # Only map meaningful text to save AI confusion
                original_strings[str(idx)] = t.text
                
        # Ask AI to define replacements
        llm = ChatOpenAI(
            model=model_id,
            openai_api_key='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',
            openai_api_base='https://openrouter.ai/api/v1',
            max_tokens=3000,
        )
        
        sys_prompt = '''You are a strict data-replacement bot. Create a Resume.
The user gives you "Profile Data" and a "Template Text Map" with integer IDs mapping to sample text.
Return ONLY a valid JSON dictionary mapping the EXACT SAME IDs to the new replaced string.
Rules:
1. Replace fake names, job titles, companies, descriptions, and skills with reality from the Profile Data.
2. If it's a generic word like "Education", "Experience", or bullet points, leave it as is.
3. Keep the text chunking literal (if ID 1 is "John " and ID 2 is "Doe", return "Linus " and "Torvalds").
4. If there is more dummy experience/projects than real ones, replace the extra with whitespace ' '.
5. Return strictly raw JSON. No markdown wrappers. Nothing else.'''
        
        usr_prompt = f"Profile Data: {json.dumps(profile_data)}\n\nTemplate Text map:\n{json.dumps(original_strings)}"
        
        response = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=usr_prompt)])
        
        # Clean response
        res_str = response.content.strip()
        import re
        res_str = re.sub(r"^```(?:json)?\s*", "", res_str, flags=re.IGNORECASE)
        res_str = re.sub(r"\s*```$", "", res_str)
        
        replacements = json.loads(res_str.strip())
        
        # Apply replacements to the XML tree exactly
        for idx, t in enumerate(text_elements):
            if str(idx) in replacements:
                t.text = replacements[str(idx)]
                
        new_xml_content = ET.tostring(tree, encoding='unicode')
        
        # Package into new virtual DOCX
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name
            
        with zipfile.ZipFile(doc_path, 'r') as zin, zipfile.ZipFile(tmp_path, 'w') as zout:
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item, new_xml_content)
                else:
                    zout.writestr(item, zin.read(item.filename))
                    
        # Encode file to Base64 for download
        with open(tmp_path, 'rb') as f:
            docx_b64 = base64.b64encode(f.read()).decode('utf-8')
            
        os.remove(tmp_path)
        
        return jsonify({
            "status": "success",
            "docx_base64": docx_b64
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    data = request.json
    messages_data = data.get('messages', [])
    model_alias = data.get('model', 'ramudu')
    
    # Map the custom alias back to the real openrouter model
    actual_model = MODEL_MAPPING.get(model_alias, "liquid/lfm-2.5-1.2b-instruct:free")
    
    # Store the API key securely on the backend instead of the frontend
    OPENROUTER_API_KEY = "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"
    
    try:
        # Initialize LangChain using ChatOpenAI wrapper for OpenRouter compatibility
        llm = ChatOpenAI(
            model=actual_model,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=1000,
        )
        
        # Parse history into LangChain message objects
        lc_messages = []
        for m in messages_data:
            if m['role'] == 'system':
                lc_messages.append(SystemMessage(content=m['content']))
            elif m['role'] == 'user':
                lc_messages.append(HumanMessage(content=m['content']))
            elif m['role'] == 'assistant' or m['role'] == 'bot':
                lc_messages.append(AIMessage(content=m['content']))
                
        # Invoke LangChain pipeline
        response = llm.invoke(lc_messages)
        
        # Package identically to standard openrouter json for compatibility with our UI
        return jsonify({
            "status": "success",
            "choices": [
                {
                    "message": {
                        "content": response.content
                    }
                }
            ]
        })
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

# 1. LinkedIn Profile Scraper
# Note: LinkedIn has strict anti-scraping measures. A real scraper typically requires login cookies.
# For simplicity, we provide a placeholder or basic Selenium structure that you'd need to extend.
@app.route('/api/linkedin', methods=['GET'])
def scrape_linkedin():
    # When using linkedin-api, you need email and password to construct a session.
    # To use li_at cookie, we can mock the Linkedin initialization slightly differently, 
    # but the simplest robust way with linkedin-api is to login with credentials or provide cookies dict if possible.
    # The library doesn't expose a straightforward way to just passing an li_at string in a clean way without JSESSIONID
    # So we'll instruct the user to provide their LinkedIn username and password in the headers or as params for testing (in a real app this should be POST + body)
    
    profile_username = request.args.get('query')
    linkedin_email = request.args.get('email')
    linkedin_password = request.args.get('password')
    cookie_li_at = request.args.get('cookie')
    
    if not profile_username:
        return jsonify({"error": "Missing profile query parameter"}), 400
        
    if not cookie_li_at and not (linkedin_email and linkedin_password):
        return jsonify({
            "status": "success",
            "source": "linkedin-api (Placeholder)",
            "message": f"Successfully received request for {profile_username}.",
            "note": "NO CREDENTIALS PROVIDED. The LinkedIn API library requires your regular LinkedIn Email and Password, OR a valid 'li_at' AND 'JSESSIONID' cookie combo in the underlying library. Please provide email and password in the UI to perform a real API authentication.",
            "profile": {
                 "url": profile_username,
                 "name": "LinkedIn User",
                 "headline": "Software Engineer"
            }
        })
        
    try:
        # Initialize the API
        # Using linkedin-api is heavily reliant on passing email and password so it can emulate the mobile app.
        if linkedin_email and linkedin_password:
             api = Linkedin(linkedin_email, linkedin_password)
        else:
             # The linkedin_api package fundamentally requires an email and password to initialize its session
             # Even if we pass cookies manually to its inner `requests.Session`, it is not officially supported by the wrapper wrapper signature.
             return jsonify({"error": "The new `linkedin-api` method requires an Account Email and Password for authentication to emulate the LinkedIn Mobile app."}), 400

        # Now fetch the target user's profile
        profile = api.get_profile(profile_username)
        
        # Get posts
        posts_data = api.get_profile_posts(profile_username)
        
        return jsonify({
            "status": "success",
            "source": "linkedin-api (Mobile Emulation)",
            "message": f"Successfully fetched profile for {profile_username}",
            "data": {
                "profile": profile,
                "recent_posts": posts_data
            }
        })
    except Exception as e:
        return jsonify({"error": str(e), "message": "Remember to use your LinkedIn 'username' (not the full URL) in the query box."}), 500

# 2. GitHub Profile (ghprofile equivalent)
# You can use the public GitHub API or a custom scraper
@app.route('/api/github', methods=['GET'])
def scrape_github():
    username = request.args.get('query')
    if not username:
        return jsonify({"error": "Missing query parameter"}), 400
    
    try:
        # 1. Fetch User Data
        gh_response = requests.get(f'https://api.github.com/users/{username}')
        if gh_response.status_code != 200:
            return jsonify({"error": f"GitHub API returned {gh_response.status_code}"}), gh_response.status_code
            
        user_data = gh_response.json()
        
        # 2. Fetch Top Repositories
        repos_response = requests.get(f'https://api.github.com/users/{username}/repos?sort=updated&per_page=5')
        repo_data_list = []
        
        if repos_response.status_code == 200:
            repos = repos_response.json()
            for repo in repos:
                repo_info = {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "stars": repo.get("stargazers_count"),
                    "language": repo.get("language"),
                    "url": repo.get("html_url"),
                    "readme_preview": ""
                }
                
                # 3. Fetch README for each repo (truncated to save token limits)
                readme_url = f'https://api.github.com/repos/{username}/{repo.get("name")}/readme'
                readme_res = requests.get(readme_url, headers={'Accept': 'application/vnd.github.v3.raw'})
                
                if readme_res.status_code == 200:
                    repo_info["readme_preview"] = readme_res.text[:1000] + "\n...[truncated]"
                else:
                    repo_info["readme_preview"] = "No README available."
                    
                repo_data_list.append(repo_info)
                
        user_data["top_repositories_with_readme"] = repo_data_list

        return jsonify({
             "status": "success",
             "source": "ghprofile",
             "data": user_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. LeetCode Data Scraper (leetcode_data_scrapper)
# Uses LeetCode's public GraphQL API
@app.route('/api/leetcode', methods=['GET'])
def scrape_leetcode():
    username = request.args.get('query')
    if not username:
         return jsonify({"error": "Missing query parameter"}), 400
    
    url = "https://leetcode.com/graphql"
    query = """
    query userPublicProfile($username: String!) {
        matchedUser(username: $username) {
            username
            githubUrl
            twitterUrl
            linkedinUrl
            profile {
                realName
                userAvatar
                birthday
                ranking
                reputation
                websites
                countryName
                company
                school
                skillTags
                aboutMe
            }
        }
    }
    """
    
    try:
        response = requests.post(url, json={"query": query, "variables": {"username": username}})
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "source": "leetcode_data_scrapper", 
                "data": response.json().get('data', {}).get('matchedUser', {})
            })
        return jsonify({"error": "Failed to fetch from LeetCode"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. GetCP (Codeforces/CP) 
# Uses Codeforces Public API
@app.route('/api/getcp', methods=['GET'])
def getcp():
    handle = request.args.get('query')
    if not handle:
         return jsonify({"error": "Missing query parameter"}), 400
         
    try:
        response = requests.get(f"https://codeforces.com/api/user.info?handles={handle}")
        if response.status_code == 200:
             return jsonify({
                 "status": "success",
                 "source": "getcp",
                 "data": response.json()
             })
        return jsonify({"error": "Failed to fetch from Codeforces"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. Competitive Programming Score API
# A hypothetical unified CP score aggregator API endpoint
@app.route('/api/cpscore', methods=['GET'])
def get_cp_score():
    username = request.args.get('query')
    if not username:
         return jsonify({"error": "Missing query parameter"}), 400
         
    # Mocked aggregator logic
    return jsonify({
         "status": "success",
         "source": "Competitive_Programming_Score_API",
         "username": username,
         "total_score": 5430,
         "breakdown": {
             "codeforces_rating": 1500,
             "leetcode_rating": 1800,
             "codechef_rating": 2130
         }
    })

# 6. HackerRank WebScraping Selenium
@app.route('/api/hackerrank', methods=['GET'])
def scrape_hackerrank():
    username = request.args.get('query')
    if not username:
         return jsonify({"error": "Missing query parameter"}), 400

    # Using Selenium in headless mode to scrape HackerRank
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Setup webdriver manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        url = f"https://www.hackerrank.com/{username}"
        driver.get(url)
        time.sleep(3) # Wait for JS to render
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        driver.quit()
        
        # Very basic parsing based on HackerRank profile classes
        name_tag = soup.find('h1', class_='profile-heading')
        name = name_tag.text.strip() if name_tag else username
        
        # This is a basic demonstration of grabbing the html via Selenium. 
        # Detailed xpath/css selectors depend on exact HackerRank DOM.
        
        return jsonify({
            "status": "success",
            "source": "Hackerrank-WebScraping-Selenium",
            "extracted_data": {
                "username": username,
                "profile_name": name,
                "url": url,
                "note": "Fetched using Selenium headless browser."
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
