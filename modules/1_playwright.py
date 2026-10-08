from load_django import *
from parser_app.models import *

from playwright.sync_api import sync_playwright

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

def parse() -> dict:
    result = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page()
        page.goto("https://brain.com.ua/")

        search = page.locator("xpath=//input[@placeholder='Знайти...']").locator("visible=true")
        search.fill("Apple iPhone 15 128GB Black")
        search.press("Enter")
        page.wait_for_load_state()
        first = page.locator("xpath=//a[contains(@href, 'Apple_iPhone_15')]").first
        first.click()
        title = page.locator("xpath=//h1").locator("visible=true").first.inner_text().strip()
        result["title"] = title
        imgs = page.locator(
            "xpath=//div[contains(concat(' ', normalize-space(@class), ' '), ' slick-slide ')"
            " and not(contains(concat(' ', normalize-space(@class), ' '), ' slick-cloned '))]"
            "//img[contains(concat(' ', normalize-space(@class), ' '), ' br-main-img ')]"
        )
        imgs.first.wait_for(state="attached")
        urls = [img.get_attribute("src") for img in imgs.all()]
        result["images"] = list(dict.fromkeys(u for u in urls if u))
        stats = page.locator(
            "xpath=//div[contains(concat(' ', normalize-space(@class), ' '), ' br-pr-chr-item ')]/div/div"
        )
        for stat in stats.all():
            name = stat.locator("xpath=.//span").first.text_content()
            value = stat.locator("xpath=.//span").last.text_content()
            result[" ".join(name.split())] = " ".join(value.split())

        browser.close()
        return result

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
    data = parse()
    product = save_data(data)
    for key, val in data.items():
        print(f"{key} - {val}")