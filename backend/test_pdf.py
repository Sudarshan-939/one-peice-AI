from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions
import tempfile
import os

html_content = "<html><body><h1>Test PDF</h1><p>Real PDF from selenium.</p></body></html>"

try:
    # 1. Write HTML to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
        
    print("Temp path:", temp_path)
    
    # 2. Setup Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 3. Load temp file
    driver.get("file:///" + temp_path.replace("\\", "/"))
    
    # 4. Print to PDF
    print_options = PrintOptions()
    print_options.background = True
    base64_pdf = driver.print_page(print_options)
    
    print("PDF base64 length:", len(base64_pdf))
    
    # 5. Cleanup
    driver.quit()
    os.remove(temp_path)
    
    print("SUCCESS")
    
except Exception as e:
    print("ERROR:", e)
