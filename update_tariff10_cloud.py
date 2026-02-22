import boto3
import requests
import random
import re
import os
from collections import defaultdict
from urllib.parse import urlparse, urlunparse, quote, unquote

# ===== ЯНДЕКС CLOUD S3 (ТАРИФ 10) =====
ACCESS_KEY = os.getenv('YANDEX_ACCESS_KEY')
SECRET_KEY = os.getenv('YANDEX_SECRET_KEY')

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='ru-central1'
)

# ===== ТОЛЬКО ПРИОРИТЕТНЫЕ ИСТОЧНИКИ (БЕЗ SNI/CIDR!) =====
PRIORITY_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
]

HEADER_TARIF10 = """#profile-title: base64:8J+ktCBTUEVDVEVSIFZQTg== 
#profile-update-interval: 12"""

# ══════════════════════════════════════════════════════════════════
#  РЕНЕЙМ
# ══════════════════════════════════════════════════════════════════
COUNTRY_RU = {
    "🇩🇪": "Германия",       "🇺🇸": "США",             "🇬🇧": "Великобритания",
    "🇫🇷": "Франция",        "🇳🇱": "Нидерланды",      "🇸🇬": "Сингапур",
    "🇯🇵": "Япония",         "🇰🇷": "Корея",           "🇨🇦": "Канада",
    "🇦🇺": "Австралия",      "🇷🇺": "Россия",          "🇫🇮": "Финляндия",
    "🇸🇪": "Швеция",         "🇳🇴": "Норвегия",        "🇩🇰": "Дания",
    "🇨🇭": "Швейцария",      "🇦🇹": "Австрия",         "🇧🇪": "Бельгия",
    "🇮🇪": "Ирландия",       "🇵🇱": "Польша",          "🇨🇿": "Чехия",
    "🇭🇺": "Венгрия",        "🇷🇴": "Румыния",         "🇧🇬": "Болгария",
    "🇭🇷": "Хорватия",       "🇷🇸": "Сербия",          "🇺🇦": "Украина",
    "🇹🇷": "Турция",         "🇮🇱": "Израиль",         "🇦🇪": "ОАЭ",
    "🇮🇳": "Индия",          "🇨🇳": "Китай",           "🇭🇰": "Гонконг",
    "🇹🇼": "Тайвань",        "🇧🇷": "Бразилия",        "🇦🇷": "Аргентина",
    "🇲🇽": "Мексика",        "🇿🇦": "ЮАР",             "🇮🇸": "Исландия",
    "🇵🇹": "Португалия",     "🇪🇸": "Испания",         "🇮🇹": "Италия",
    "🇬🇷": "Греция",         "🇲🇩": "Молдова",         "🇱🇹": "Литва",
    "🇱🇻": "Латвия",         "🇪🇪": "Эстония",         "🌐": "Anycast",
}

COUNTRY_NAMES_EN = {
    "germany": "Германия",        "united states": "США",         "united kingdom": "Великобритания",
    "france": "Франция",          "netherlands": "Нидерланды",    "singapore": "Сингапур",
    "japan": "Япония",            "korea": "Корея",               "canada": "Канада",
    "australia": "Австралия",     "russia": "Россия",             "finland": "Финляндия",
    "sweden": "Швеция",           "norway": "Норвегия",           "denmark": "Дания",
    "switzerland": "Швейцария",   "austria": "Австрия",           "belgium": "Бельгия",
    "ireland": "Ирландия",        "poland": "Польша",             "czech": "Чехия",
    "hungary": "Венгрия",         "romania": "Румыния",           "bulgaria": "Болгария",
    "croatia": "Хорватия",        "serbia": "Сербия",             "ukraine": "Украина",
    "turkey": "Турция",           "israel": "Израиль",            "india": "Индия",
    "china": "Китай",             "hong kong": "Гонконг",         "taiwan": "Тайвань",
    "brazil": "Бразилия",         "argentina": "Аргентина",       "mexico": "Мексика",
    "spain": "Испания",           "italy": "Италия",              "greece": "Греция",
    "iceland": "Исландия",        "portugal": "Португалия",       "estonia": "Эстония",
    "lithuania": "Литва",         "latvia": "Латвия",             "moldova": "Молдова",
    "anycast": "Anycast",
}

CODE_TO_FLAG = {
    "DE": "🇩🇪", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "NL": "🇳🇱",
    "SG": "🇸🇬", "JP": "🇯🇵", "KR": "🇰🇷", "CA": "🇨🇦", "AU": "🇦🇺",
    "RU": "🇷🇺", "FI": "🇫🇮", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰",
    "CH": "🇨🇭", "AT": "🇦🇹", "BE": "🇧🇪", "IE": "🇮🇪", "PL": "🇵🇱",
    "CZ": "🇨🇿", "HU": "🇭🇺", "RO": "🇷🇴", "BG": "🇧🇬", "HR": "🇭🇷",
    "RS": "🇷🇸", "UA": "🇺🇦", "TR": "🇹🇷", "IL": "🇮🇱", "AE": "🇦🇪",
    "IN": "🇮🇳", "CN": "🇨🇳", "HK": "🇭🇰", "TW": "🇹🇼", "BR": "🇧🇷",
    "AR": "🇦🇷", "MX": "🇲🇽", "ZA": "🇿🇦", "IS": "🇮🇸", "PT": "🇵🇹",
    "ES": "🇪🇸", "IT": "🇮🇹", "GR": "🇬🇷", "MD": "🇲🇩", "LT": "🇱🇹",
    "LV": "🇱🇻", "EE": "🇪🇪",
}

def get_flag_and_country(fragment: str):
    decoded = unquote(fragment)
    flag_match = re.search(r'([\U0001F1E0-\U0001F1FF]{2}|\U0001F310)', decoded)
    if flag_match:
        flag = flag_match.group(1)
        if flag in COUNTRY_RU:
            return flag, COUNTRY_RU[flag]
    decoded_lower = decoded.lower()
    for eng, rus in COUNTRY_NAMES_EN.items():
        if eng in decoded_lower:
            for code, name in COUNTRY_RU.items():
                if name == rus and code in CODE_TO_FLAG:
                    return CODE_TO_FLAG[code], rus
            return "🌐", rus
    return "🌐", "Сервер"

def rename_key(line: str, label: str) -> str:
    line = line.strip()
    if not line or line.startswith("#"):
        return line
    for proto in ["vless://", "vmess://", "trojan://", "ss://", "ssr://", "hysteria2://", "tuic://"]:
        if line.lower().startswith(proto):
            break
    else:
        return line
    try:
        parsed = urlparse(line)
        flag, country = get_flag_and_country(parsed.fragment)
        new_name = f"{flag} {country} - {label}"
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, parsed.query, quote(new_name)
        ))
    except Exception:
        return line

def rename_block(configs: list, label: str) -> list:
    return [rename_key(line, label) for line in configs]

# ══════════════════════════════════════════════════════════════════
#  ФИЛЬТРЫ (без изменений)
# ══════════════════════════════════════════════════════════════════

def is_cloudflare(config):
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def extract_country(config):
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/', '🇩🇪', 'germani'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/', '🇳🇱', 'niderland'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/', '🇫🇷', 'french'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/', '🇷🇺', 'russian'],
        'FI': ['fi-', 'finland', 'fi:', 'helsinki', '🇫🇮'],
        'US': ['us-', 'usa', 'us:', 'newyork', '🇺🇸'],
        'SG': ['sg-', 'singapore', 'sg:', '🇸🇬'],
        'GB': ['gb-', 'uk', 'gb:', 'london', '🇬🇧'],
        'CA': ['ca-', 'canada', 'ca:', 'toronto', '🇨🇦'],
        'SE': ['se-', 'sweden', 'se:', 'stockholm', '🇸🇪']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

# ══════════════════════════════════════════════════════════════════
#  ОСНОВНОЙ СКРИПТ
# ══════════════════════════════════════════════════════════════════

print("🚀 SPECTER VPN Тариф 10 — 3DE/3NL/3FR/2RU + 6 случайных!")

# ── 1. ФИКСИРОВАННЫЕ БЛОКИ: 3/3/3/2 ─────────────────────────────
target_blocks = {'DE': 3, 'NL': 3, 'FR': 3, 'RU': 2}
collected_blocks = {country: [] for country in target_blocks}

print("\n📥 СОБИРАЕМ ФИКСИРОВАННЫЕ БЛОКИ:")
for i, source in enumerate(PRIORITY_SOURCES):
    print(f"  {i+1}. {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        valid_lines = [l for l in lines if not is_cloudflare(l)]

        for country, target_count in target_blocks.items():
            if len(collected_blocks[country]) < target_count:
                country_lines = [l for l in valid_lines if extract_country(l) == country]
                needed = target_count - len(collected_blocks[country])
                if country_lines:
                    selected = random.sample(country_lines, min(needed, len(country_lines)))
                    for key in selected:
                        if key not in collected_blocks[country]:
                            collected_blocks[country].append(key)
                    print(f"     ✅ {country}: +{len(selected)} (всего {len(collected_blocks[country])}/{target_count})")
    except:
        print(f"     ❌")

# Переименовываем → WiFi
for country in collected_blocks:
    collected_blocks[country] = rename_block(collected_blocks[country], "WiFi")

# ── 2. 6 СЛУЧАЙНЫХ РАЗНЫХ СТРАН ──────────────────────────────────
print("\n📥 6 СЛУЧАЙНЫХ СТРАН (по 1 с каждой):")
random_countries = defaultdict(list)
used_countries = set(collected_blocks.keys())

for source in PRIORITY_SOURCES:
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        valid_lines = [l for l in lines if not is_cloudflare(l)]

        for line in valid_lines:
            country = extract_country(line)
            if (country not in used_countries and
                country != 'OTHER' and
                len(random_countries[country]) < 1):
                random_countries[country].append(line)
    except:
        pass

random_countries_list = list(random_countries.keys())
random.shuffle(random_countries_list)
selected_random = random_countries_list[:6]

# Переименовываем → WiFi
for country in selected_random:
    random_countries[country] = rename_block(random_countries[country][:1], "WiFi")

# ── 3. ФИНАЛЬНАЯ СБОРКА ───────────────────────────────────────────
final_configs = []

print("\n🎯 СОБИРАЕМ ТАРИФ 10 (17 серверов):")
for country in ['DE', 'NL', 'FR', 'RU']:
    block = collected_blocks[country]
    final_configs.extend(block)
    print(f"✅ БЛОК {country}: {len(block)} серверов")

for country in selected_random:
    block = random_countries[country][:1]
    final_configs.extend(block)
    print(f"✅ СЛУЧАЙНАЯ {country}: 1 сервер")

final_configs = final_configs[:17]
content = HEADER_TARIF10 + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print("📋 3DE + 3NL + 3FR + 2RU + 6 случайных = 17")

# ── 4. ЗАГРУЗКА В S3 ──────────────────────────────────────────────
try:
    s3_client.put_object(
        Bucket='tariff10',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ТАРИФ 10 ЗАГРУЖЕН!")
    print("🔗 Happ: https://storage.yandexcloud.net/tariff10/отобранные.txt")
    print("🎉 НАЗВАНИЕ: SPECTER VPN Tariff 10!")
except Exception as e:
    print(f"❌ {e}")

print("\n🎉 ТАРИФ 10 — 3/3/3/2 + 6 случайных готов!")
