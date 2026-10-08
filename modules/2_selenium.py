from load_django import *
from parser_app.models import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)


FIELD_MAP = {
    "Форм-фактор": "form_factor",
    "Кількість SIM-карт": "sim_count",
    "Формат SIM-карти": "sim_format",
    "Покоління зв'язку (2G /3G/4G/5G)": "network_generation",
    "Операційна система": "os",
    "Тип дисплея": "display_type",
    "Діагональ екрану": "screen_diagonal",
    "Роздільна здатність екрану": "screen_resolution",
    "Частота оновлення екрану": "refresh_rate",
    "Процесор": "processor",
    "Кількість ядер": "cpu_cores",
    "Вбудована пам'ять": "storage",
    "Кількість модулів основної камери": "main_camera_modules",
    "Основна камера": "main_camera",
    "Діафрагма основної камери": "main_camera_aperture",
    "Метод стабілізації": "stabilization",
    "Запис відео основної камери": "video_recording",
    "Кількість модулів фронтальної камери": "front_camera_modules",
    "Фронтальна камера": "front_camera",
    "Діафрагма фронтальної камери": "front_camera_aperture",
    "Функції камери": "camera_features",
    "Мультимедіа": "multimedia",
    "Органайзер": "organizer",
    "Бездротові технології": "wireless",
    "Навігація": "navigation",
    "Інтерфейси і підключення": "interfaces",
    "Особливості": "features",
    "Вбудовані датчики": "sensors",
    "Безпека": "security",
    "Оснащення": "equipment",
    "Стан товару": "condition",
    "Розміри (мм)": "dimensions",
    "Вага": "weight",
    "Колір": "color",
    "Особливості корпусу": "body_features",
    "Виробник": "manufacturer",
    "Країна виробництва": "country",
    "Гарантія, міс": "warranty_months",
    "Штрихкод": "barcode",
    "Примітка": "note",
}

def cls(name: str) -> str:
    return f"contains(concat(' ', normalize-space(@class), ' '), ' {name} ')"


def first_visible(driver, xpath: str):
    for el in driver.find_elements(By.XPATH, xpath):
        if el.is_displayed():
            return el
    raise NoSuchElementException(f"No visible element found: {xpath}")

def parse() -> dict:
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    long_wait = WebDriverWait(driver, 120)
    result = {}
    try:
        driver.get("https://brain.com.ua/")
        try:
            search_input = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@type='search']"))
            )
            search_input.send_keys("Apple iPhone 15 128GB Black")
            first_visible(driver, "//input[@type='submit']").click()
        except (TimeoutException, NoSuchElementException) as e:
            raise RuntimeError(f"Failed to perform search: {e}") from e
        try:
            long_wait.until(lambda d: "Just a moment" not in d.title)
        except TimeoutException as e:
            raise RuntimeError("Cloudflare did not let us through within 120 seconds") from e
        try:
            first_link = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href, 'Apple_iPhone_15')]")
                )
            )
            first_link.click()
        except TimeoutException as e:
            raise RuntimeError("Product link not found") from e
        try:
            first_visible(driver, "//a[@href='#br-characteristics']").click()
        except (NoSuchElementException, WebDriverException) as e:
            print(f"Characteristics tab was not clicked: {e}")
        try:
            wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//h3[contains(., 'Основні характеристики')]")
                )
            )
        except TimeoutException as e:
            raise RuntimeError("Characteristics block did not appear") from e
        try:
            result["title"] = first_visible(driver, "//h1").text.strip()
        except NoSuchElementException as e:
            raise RuntimeError("Product title not found") from e
        for spec in driver.find_elements(By.XPATH, f"//div[{cls('br-pr-chr-item')}]"):
            rows = spec.find_elements(By.XPATH, ".//h3/following-sibling::div[1]/div")
            for row in rows:
                try:
                    spans = row.find_elements(By.XPATH, "./span")
                    if len(spans) < 2:
                        continue
                    key = " ".join(spans[0].text.split())
                    value = " ".join(spans[1].text.split())
                    if key:
                        result[key] = value
                except WebDriverException as e:
                    print(f"Skipped characteristics row: {e}")
        image_urls = []
        try:
            for img in driver.find_elements(By.XPATH, f"//img[{cls('br-main-img')}]"):
                src = img.get_attribute("src")
                if src and src not in image_urls:
                    image_urls.append(src)
        except WebDriverException as e:
            print(f"Error while collecting images: {e}")
        result["images"] = image_urls

        return result

    finally:
        driver.quit()

def save_data(data: dict):
    fields = {
        "title": data.get("title", ""),
        "images": data.get("images", []),
    }

    for key, value in data.items():
        if key in ("title", "images"):
            continue
        if key in FIELD_MAP:
            fields[FIELD_MAP[key]] = value
        else:
            continue

    warranty = fields.get("warranty_months")
    if warranty is not None:
        try:
            fields["warranty_months"] = int(warranty)
        except (TypeError, ValueError):
            fields["warranty_months"] = None

    return Product.objects.create(**fields)

if __name__ == '__main__':
    result = parse()
    save_data(result)
    for key, val in result.items():
        print(f"{key} - {val}")


