from load_django import *
from parser_app.models import *

import requests
from bs4 import BeautifulSoup

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

def clean(el):
    return " ".join(el.get_text().split())

def parse() -> dict:
    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Cookie": "PHPSESSID=rrod0441j89emmkcnoiqdb30gt; Lang=ua; CityID=23562; entryRef=www.google.com; entryPage=%2Fukr%2F; sc=690B3565-020F-1F0E-94CD-70997023E350; cf_clearance=kLBQlcZ6LCdsyu53gqJK8ZMd0kUMqZbtduquAA3wUmg-1791290218-1.2.1.1-U8V9T36VGM.JURBGfGo58E4bYZfsVRAwjbKgYqXZMKp74kRxShDg2.Uhb8bfDanRFOjmJF1wrn4ZarxYhooHRF2uDIjzVqthrDiJOVhANLBME3eRtdefJvnWkaFQ9.KFC5QvyWESbmjm41nKwdqa64SjgfXoI26_cArbcNWCVKcpU08kkUU8adHhVnROrvoDucbfDd6OaV9jP.OZNf0AbSnqlWCDRNhhv_LhSb64Afi_gcEiNETBlhGyN8qolngUXib4zshxEVgsp86t9tmdRtooibzUMOefCvjOawgSmVV8F1LStG5.OB2eBZQjPHs05jjyYQECZdzTKkubLpyUEmQxD5ITx4cWHVN.JP5kIX4",
        "Host": "brain.com.ua",
        "Referer": "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html",
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
    }
    resp = requests.get(
        "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html",
        headers=headers,
    )
    raw_html = resp.text
    soup = BeautifulSoup(raw_html, "html.parser")
    result = {}
    title = soup.select_one("h1.desktop-only-title")
    result["title"] = title.get_text().strip()
    images = []
    for img in soup.select("img.br-main-img"):
        src = img.get("src") or img.get("data-src")
        if src and src not in images:
            images.append(src)
    result["images"] = images

    for item in soup.select("#br-characteristics .br-pr-chr-item"):
        for row in item.select("h3 + div > div"):
            spans = row.find_all("span", recursive=False)
            if len(spans) != 2:
                continue
            name, val = clean(spans[0]), clean(spans[1])
            result[name] = val
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
    result = parse()
    save_data(result)
    for key, val in result.items():
        print(f"{key} - {val}")

