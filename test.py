import os
import time
import pandas as pd
from functions import categorize_review
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Configuration
# -------------------------
URL_SCHOOL = "https://careerkarma.com/schools/4geeks-academy/"
EMAIL = os.getenv("CK_EMAIL")
PASSWORD = os.getenv("CK_PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError("Please set CK_EMAIL and CK_PASSWORD environment variables.")

# -------------------------
# Selenium Setup
# -------------------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--headless=new")  # remove if debugging
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# -------------------------
# 1️⃣ Log in
# -------------------------
driver.get("https://careerkarma.com/sign-in/")

wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(EMAIL)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.CSS_SELECTOR, "button[data-qa='sign-in-form_sign-in-btn']").click()

wait.until(EC.url_contains("careerkarma.com"))
print("✅ Logged in successfully")

# -------------------------
# 2️⃣ Navigate to School Page and Reviews
# -------------------------
driver.get(URL_SCHOOL)
reviews_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Reviews')]")))
reviews_tab.click()
time.sleep(2)

# Click "See all reviews" if present
try:
    see_all_btn = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='schools-page_reviews-section_see-all-reviews-btn']"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", see_all_btn)
    driver.execute_script("arguments[0].click();", see_all_btn)
    print("➡️ Clicked 'See all reviews'")
    time.sleep(2)
except:
    print("⚠️ 'See all reviews' button not found, proceeding...")

# -------------------------
# 3️⃣ Load all reviews
# -------------------------
prev_count = 0
while True:
    reviews = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='schools-page_reviews-section_school-review']")
    current_count = len(reviews)

    try:
        load_more_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='schools-page_reviews-section_load-more-btn']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
        driver.execute_script("arguments[0].click();", load_more_btn)
        print("➡️ Clicked 'Load More'")
        time.sleep(2)

        reviews = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='schools-page_reviews-section_school-review']")
        if len(reviews) == prev_count:
            print("✅ All reviews loaded, no new reviews appeared.")
            break
        prev_count = len(reviews)

    except:
        print("✅ 'Load More' button not found or clickable, ending loop.")
        break

print(f"Total reviews loaded: {len(reviews)}")

# -------------------------
# 4️⃣ Expand all "See more" texts
# -------------------------
for see_more in driver.find_elements(By.CSS_SELECTOR, "label.sc-86822f03-0"):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", see_more)
        driver.execute_script("arguments[0].click();", see_more)
        time.sleep(0.1)
    except:
        continue
print("✅ All review texts expanded")

# -------------------------
# 5️⃣ Parse reviews into DataFrame
# -------------------------
review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='schools-page_reviews-section_school-review']")
print(f"Processing {len(review_elements)} reviews...")

reviews_data = []

for idx, review_el in enumerate(review_elements, start=1):
    soup_card = BeautifulSoup(review_el.get_attribute("outerHTML"), "html.parser")

    # --- Static fields ---
    name_tag = soup_card.select_one("span.sc-aefd771a-3")
    if name_tag:
        # Take only the first direct text node (before "graduated" or links)
        raw_name = name_tag.contents[0].strip()
        name = raw_name.split("graduated")[0].strip()
    else:
        name = "N/A"


    role_tag = soup_card.select_one("span.sc-aefd771a-3 span")
    role = role_tag.get_text(strip=True) if role_tag else "N/A"

    date_tag = soup_card.select_one("div.sc-18449bc4-1")
    date = date_tag.get_text(strip=True) if date_tag else "N/A"

    title_tag = soup_card.select_one("p.sc-18449bc4-4")
    title = title_tag.get_text(strip=True) if title_tag else "N/A"

    review_text_tag = soup_card.select_one("div.sc-18449bc4-21")
    review_text = review_text_tag.get_text(strip=True) if review_text_tag else "N/A"

    # --- Only overall rating ---
    try:
        overall_star_imgs = review_el.find_elements(By.CSS_SELECTOR, "img[alt='star'][type='review']")
        overall = sum(1 for img in overall_star_imgs if "star-checked" in img.get_attribute("src"))
    except:
        overall = "N/A"

    # Append row
    reviews_data.append({
        "Name": name,
        "Role": role,
        "Date": date,
        "Title": title,
        "Review": review_text,
        "Overall": overall
    })

    print(f"✅ Processed review {idx}/{len(review_elements)}")

# Convert to DataFrame
df = pd.DataFrame(reviews_data)
print("✅ Reviews saved to DataFrame")

# Apply categorization and expand dictionary into separate columns
category_df = df.apply(
    lambda row: pd.Series(categorize_review(row.get("title"), row.get("Review"))),
    axis=1
)

# Concatenate category columns with original DataFrame
df = pd.concat([df, category_df], axis=1)

# Optional: Save to CSV
df.to_csv("careerkarma_reviews.csv", index=False, encoding="utf-8")
print("✅ DataFrame also written to careerkarma_reviews.csv")

driver.quit()
