# 🏴‍☠️ One-Piece AI Developer Tool Suite

An advanced, interactive developer workspace combining **AI LLM Chat Testing (OpenRouter API)**, **Multi-Source Developer Profile Scrapers**, and **AI-Powered Resume Generators** (supporting HTML, PDF, and DOCX outputs).

---

## 🚀 Key Features

### 1. Dev Tools API Tester (`index.html`)
- **Multi-Model LLM Testing**: Chat and test prompt performance across several model aliases via a secure proxy:
  - **Ramudu**: Liquid LFM 2.5 1.2B Instruct (`liquid/lfm-2.5-1.2b-instruct:free`)
  - **Bemudu**: Arcee-AI Trinity Large Preview (`arcee-ai/trinity-large-preview:free`)
  - **Surudu**: Stepfun 3.5 Flash (`stepfun/step-3.5-flash:free`)
- **System Prompt Tuning**: Dynamically configure the system instructions.
- **Rich Rendering**: Full Markdown output support for model responses.

### 2. Profile Scrapers & APIs (`profiles.html`)
Scrape profile metrics and activities from 6 popular platforms. Inputs are **URL-smart**; you can paste either the raw username or the full profile URL (e.g., `https://github.com/Sudarshan-939`).
- **LinkedIn Profile**: Authenticates securely using `linkedin-api` to pull contact info, headlines, summary, and recent posts.
- **GitHub Profile**: Extracts bio, stats, and top 5 repositories alongside an AI-friendly truncated preview of their READMEs.
- **LeetCode Data**: Connects with LeetCode's official GraphQL backend to pull user ranking, reputation, and skill tags.
- **GetCP (Codeforces)**: Fetches competitive programming stats (rating, rank, etc.) using Codeforces' public APIs.
- **CP Score Aggregator**: Combines ratings across Codeforces, LeetCode, and CodeChef into a unified score.
- **HackerRank Scraper**: Headless Selenium-based scraper that extracts user profile information.

### 3. AI Resume & CV Builder
- **HTML Resume Generation**: Feeds scraped profile JSON into an AI prompt to construct a responsive, stylish single-page HTML resume.
- **Native PDF Export**: Renders the generated HTML within a headless Chrome browser page via Selenium to print and download a pixel-perfect, native PDF.
- **DOCX Template Replacement**: Takes standard DOCX templates, parses their XML structure, uses LLMs to perform smart word-chunk mapping/replacements, and outputs a downloadable, professionally formatted `.docx` resume.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (Custom Dark Mode and Glassmorphic Theme), Vanilla JavaScript.
- **Backend**: Python 3.10+ with Flask & Flask-CORS.
- **LLM Orchestration**: LangChain (`langchain-openai`, `langchain-core`) via OpenRouter.
- **Web Scraping & Automation**: BeautifulSoup4, Selenium WebDriver, `linkedin-api`.
- **File Manipulation**: OpenXML parsing (`lxml.etree`), standard `zipfile` compression.

---

## 📦 Installation & Setup

### Prerequisites
1. **Python 3.10 or higher** installed.
2. **Google Chrome** installed (required by Selenium for headless printing and HackerRank scraping).

### Backend Configuration

1. Clone or navigate to the project directory:
   ```bash
   cd c:/Users/ys770/source/repos/one-peice-AI
   ```

2. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Mac/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Start the Flask development backend server:
```bash
python app.py
```

The server runs on `http://127.0.0.1:5000` (or your local IP address `http://192.168.1.X:5000`).
Open `http://localhost:5000` in your browser to view the application.

---

## 📝 API Endpoints

The Flask backend exposes the following API endpoints (all prefixes default to `/api/*`):

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/chat` | `POST` | OpenRouter proxy for LLM testing |
| `/api/github` | `GET` | Fetches parsed GitHub profile + repos + README previews |
| `/api/linkedin` | `GET` | Fetches LinkedIn profile and posts (requires email/password query params) |
| `/api/leetcode` | `GET` | Fetches LeetCode statistics via GraphQL |
| `/api/getcp` | `GET` | Fetches Codeforces handle profile statistics |
| `/api/cpscore` | `GET` | Mock API aggregating ratings from CP websites |
| `/api/hackerrank` | `GET` | Headless Selenium scraper for HackerRank profiles |
| `/api/generate_resume` | `POST` | Uses AI to generate HTML/CSS from profile JSON |
| `/api/generate_pdf` | `POST` | Headless Chrome print-to-pdf generator from HTML content |
| `/api/generate_docx` | `POST` | XML text-replacement engine for DOCX resume templates |

---

## ⚠️ Known Limitations & Troubleshooting

> [!WARNING]
> **LinkedIn Authentication Challenges**
> The `linkedin-api` library emulates a mobile app login. LinkedIn frequently blocks automated login requests, requesting a security challenge/CAPTCHA. 
> - If you encounter login failures, log into LinkedIn in your normal browser first to clear any verification prompts.
> - Double-check that your query credentials (email/password) are correct.

> [!IMPORTANT]
> **Headless Chrome and Drivers**
> The PDF generator and HackerRank scraper rely on `webdriver-manager` to automatically download the correct Chrome driver. Ensure Google Chrome is installed on your system and is allowed network access.
