from flask import Flask, request, jsonify, send_from_directory
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

# Serve frontend files from the parent directory (project root)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def load_dotenv():
    cwd = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(cwd, '..', '.env')
    if os.path.exists(dotenv_path):
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

load_dotenv()

app = Flask(__name__, static_folder=None)
CORS(app)  # Allow CORS for the frontend to hit these APIs

def extract_username(query):
    """Extract username from a full URL or return as-is if already a username."""
    if not query:
        return query
    # Strip trailing slashes
    query = query.strip().rstrip('/')
    # Handle full URLs like https://github.com/username or https://leetcode.com/username
    if '/' in query:
        # Take the last non-empty path segment
        parts = [p for p in query.split('/') if p]
        return parts[-1] if parts else query
    return query

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    # Don't intercept API routes
    if path.startswith('api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    # Only serve files that actually exist
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "File not found"}), 404

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
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    
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
            openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
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
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    
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
    profile_username = extract_username(request.args.get('query'))
    linkedin_email = request.args.get('email')
    linkedin_password = request.args.get('password')
    
    if not profile_username:
        return jsonify({"error": "Missing profile query parameter"}), 400
        
    if not (linkedin_email and linkedin_password):
        return jsonify({
            "status": "info",
            "source": "linkedin-api",
            "message": f"Request received for '{profile_username}'.",
            "note": "LinkedIn requires your Email and Password to authenticate. Please fill in the credentials fields and try again.",
            "data": {
                 "profile_url": f"https://www.linkedin.com/in/{profile_username}",
                 "username": profile_username,
                 "name": "Credentials Required",
                 "headline": "Please provide email & password to scrape"
            }
        })
        
    try:
        api = Linkedin(linkedin_email, linkedin_password)

        # Fetch the target user's profile
        profile = api.get_profile(profile_username)
        
        # Try to get posts (may fail silently)
        posts_data = []
        try:
            posts_data = api.get_profile_posts(profile_username)
        except Exception:
            pass
        
        # Clean profile data
        clean_profile = {
            "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
            "headline": profile.get("headline"),
            "summary": profile.get("summary"),
            "location": profile.get("locationName"),
            "industry": profile.get("industryName"),
            "profile_url": f"https://www.linkedin.com/in/{profile_username}",
        }
        
        return jsonify({
            "status": "success",
            "source": "linkedin-api",
            "data": {
                "profile": clean_profile,
                "recent_posts": posts_data[:5] if posts_data else []
            }
        })
    except Exception as e:
        error_msg = str(e).lower()
        
        # Provide human-readable error messages for common failures
        if "challenge" in error_msg or "captcha" in error_msg:
            user_message = "LinkedIn is requesting a CAPTCHA/security challenge. Please log into LinkedIn in your browser first, complete any verification, then try again."
        elif "bad credentials" in error_msg or "invalid" in error_msg or "401" in error_msg:
            user_message = "Invalid email or password. Please double-check your LinkedIn credentials."
        elif "too many" in error_msg or "rate" in error_msg or "429" in error_msg:
            user_message = "Too many login attempts. LinkedIn has temporarily blocked your account. Wait a few minutes and try again."
        else:
            user_message = f"LinkedIn login failed: {str(e)}. This library emulates LinkedIn's mobile app and may be blocked. Try logging into LinkedIn in your browser first to clear any security prompts."
        
        return jsonify({
            "status": "error",
            "source": "linkedin-api",
            "error": user_message,
            "data": {
                "profile_url": f"https://www.linkedin.com/in/{profile_username}",
                "username": profile_username,
                "name": "Login Failed",
                "headline": user_message
            }
        }), 200  # Return 200 so the frontend can display the error message in the UI instead of crashing

# 2. GitHub Profile (ghprofile equivalent)
# You can use the public GitHub API or a custom scraper
@app.route('/api/github', methods=['GET'])
def scrape_github():
    username = extract_username(request.args.get('query'))
    if not username:
        return jsonify({"error": "Missing query parameter"}), 400
    
    try:
        # 1. Fetch User Data
        gh_response = requests.get(f'https://api.github.com/users/{username}')
        if gh_response.status_code != 200:
            return jsonify({"error": f"GitHub API returned {gh_response.status_code}"}), gh_response.status_code
            
        user_data = gh_response.json()
        
        # Build clean profile data (no API URLs or internal IDs)
        clean_profile = {
            "name": user_data.get("name") or user_data.get("login"),
            "username": user_data.get("login"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "company": user_data.get("company"),
            "email": user_data.get("email"),
            "blog": user_data.get("blog") or None,
            "twitter": user_data.get("twitter_username"),
            "avatar_url": user_data.get("avatar_url"),
            "profile_url": user_data.get("html_url"),
            "hireable": user_data.get("hireable"),
            "joined": user_data.get("created_at", "")[:10],  # Just the date
        }
        
        clean_stats = {
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
            "public_gists": user_data.get("public_gists", 0),
        }
        
        # 2. Fetch Top Repositories
        repos_response = requests.get(f'https://api.github.com/users/{username}/repos?sort=updated&per_page=5')
        clean_repos = []
        
        if repos_response.status_code == 200:
            repos = repos_response.json()
            for repo in repos:
                repo_info = {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "url": repo.get("html_url"),
                    "readme_preview": ""
                }
                
                # 3. Fetch README for each repo (truncated to save token limits)
                readme_url = f'https://api.github.com/repos/{username}/{repo.get("name")}/readme'
                readme_res = requests.get(readme_url, headers={'Accept': 'application/vnd.github.v3.raw'})
                
                if readme_res.status_code == 200:
                    repo_info["readme_preview"] = readme_res.text[:500] + "\n...[truncated]"
                else:
                    repo_info["readme_preview"] = "No README available."
                    
                clean_repos.append(repo_info)

        return jsonify({
             "status": "success",
             "source": "ghprofile",
             "data": {
                 **clean_profile,
                 **clean_stats,
                 "top_repositories_with_readme": clean_repos
             }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. LeetCode Data Scraper (leetcode_data_scrapper)
# Uses LeetCode's public GraphQL API
@app.route('/api/leetcode', methods=['GET'])
def scrape_leetcode():
    username = extract_username(request.args.get('query'))
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
    handle = extract_username(request.args.get('query'))
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
    username = extract_username(request.args.get('query'))
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
    username = extract_username(request.args.get('query'))
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
