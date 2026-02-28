import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def scrape_linkedin_posts_selenium(username):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add a random user agent to masquerade as a real browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    url = f"https://www.linkedin.com/in/{username}/recent-activity/all/"
    print(f"Fetching {url}...")
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    driver.quit()
    
    # Let's save the page source to see if we hit an authwall
    with open("linkedin_page.html", "w", encoding="utf-8") as f:
        f.write(page_source)

    print("Title of the page:", soup.title.string if soup.title else "No title")
    print("Length of page source:", len(page_source))
    
    # Check if authwall
    if "Sign In" in soup.text or "authwall" in driver.current_url.lower() or "session_redirect" in driver.current_url.lower():
         print("Hit an Authwall!")

scrape_linkedin_posts_selenium("eddala")
