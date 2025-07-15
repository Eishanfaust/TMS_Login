from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from captcha import captcha_solver
from dotenv import load_dotenv
import os
import time
import random
import base64
import io
from PIL import Image
import datetime
import glob

#randomized delay that can be removed, just to avoid any barriers
def random_delay():
    delay = random.uniform(1, 4)
    print(f"[Delay] Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)

#convert blob URL image to base64 through JS canvas 
def get_image_base64(driver, img_element):
    script = """
    const img = arguments[0];
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    return canvas.toDataURL('image/png').substring(22);
    """
    return driver.execute_script(script, img_element)

#clean imges in the captcha folder
def clean_captcha_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*.png"))
    for f in files:
        try:
            os.remove(f)
            print(f"[Cleanup] Deleted old captcha file: {f}")
        except Exception as e:
            print(f"[Cleanup] Failed to delete {f}: {e}")

#load credentials
load_dotenv()
username_input = os.getenv("ID_USER")
password_input = os.getenv("PASSWORD")
tms_input = os.getenv("TMS")

if not username_input or not password_input:
    raise Exception("USERNAME or PASSWORD not set in .env")

#tms id for specific site access
tms_id = tms_input

#webdriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(), options=options)

try:
    url = f"https://tms{tms_id}.nepsetms.com.np/login"
    driver.get(url)
    random_delay()

    
    username_xpath = "/html/body/app-root/app-login/div/div/div[2]/form/div[1]/input"
    username_field = driver.find_element(By.XPATH, username_xpath)
    random_delay()
    password_xpath = "/html/body/app-root/app-login/div/div/div[2]/form/div[2]/input"
    driver.find_element(By.XPATH, password_xpath).send_keys(password_input)
    random_delay()

    #waiting for captcha image to load
    captcha_xpath = "/html/body/app-root/app-login/div/div/div[2]/form/div[3]/div[2]/div/img"
    wait = WebDriverWait(driver, 15)

    captcha_img = wait.until(EC.presence_of_element_located((By.XPATH, captcha_xpath)))
    wait.until(lambda d: captcha_img.get_attribute("src") and len(captcha_img.get_attribute("src")) > 0)

    src = captcha_img.get_attribute("src")
    print(f"[DEBUG] Captcha src: {src[:100]}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    captcha_dir = os.path.join(script_dir, "captchas")
    os.makedirs(captcha_dir, exist_ok=True)

    #clean old captcha
    clean_captcha_folder(captcha_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(captcha_dir, f"captcha_{timestamp}.png")

    #imgsrc formats
    if src.startswith("data:image"):
        base64_data = src.split(",")[1]
    elif src.startswith("blob:"):
        base64_data = get_image_base64(driver, captcha_img)
    else:
        print("[ERROR] Captcha image source format is unknown.")
        driver.quit()
        exit()

    captcha_bytes = base64.b64decode(base64_data)
    image = Image.open(io.BytesIO(captcha_bytes))
    image.save(image_path)
    print(f"[Saved] Captcha saved at: {os.path.abspath(image_path)}")

    #captcha func
    captcha_text = captcha_solver(image_path)
    print(f"[Captcha Solved] You entered: {captcha_text}")
    random_delay()

    #fill fields
    captcha_input_xpath = "/html/body/app-root/app-login/div/div/div[2]/form/div[3]/div[1]/div/input"
    driver.find_element(By.XPATH, captcha_input_xpath).send_keys(captcha_text)
    random_delay()
    login_button_xpath = "/html/body/app-root/app-login/div/div/div[2]/form/div[4]/input"
    driver.find_element(By.XPATH, login_button_xpath).click()
    print("[Login] Login button clicked.")
    time.sleep(5)
    input("Press Enter to close browser...")

finally:
    driver.quit()
