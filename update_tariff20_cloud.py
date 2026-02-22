import boto3
import requests
import random
import re
import os
from collections import defaultdict
from urllib.parse import urlparse, urlunparse, quote, unquote

# ===== ЯНДЕКС CLOUD S3 (ТАРИФ 20) =====
ACCESS_KEY = os.getenv('YANDEX_ACCESS_KEY')
SECRET_KEY = os.getenv('YANDEX_SECRET_KEY')

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='ru-central1'
)

# ===== ПРИОРИТЕТНЫЕ ИСТОЧНИКИ =====
PRIORITY_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
]

# ===== SNI/CIDR ИСТОЧНИКИ ДЛЯ ТАРИФА 20 =====
SNI_CIDR_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'
]

HEADER_TARIF20 = """#profile-title: base64:8J+ktCBTUEVDVEVSIFRhcmlmIDIw
#profile-update-interval: 12"""

# ══════════════════════════════════════════════════════════════════
#  РЕНЕЙМ — флаги, словари, функции
# ══════════════════════════════════════════════════════════════════

# Emoji флаг → русское название
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

# Английское название → русское (когда в ключе нет emoji)
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

# Код страны → emoji флаг (для fallback когда флага нет в тексте ключа)
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
    """
    Извлекает (emoji_флаг, русское_название) из fragment ключа.
    Сначала ищет emoji прямо в тексте, потом по английскому названию.
    """
    decoded = unquote(fragment)

    # 1. Ищем emoji флаг страны прямо в fragment
    flag_match = re.search(r'([\U0001F1E0-\U0001F1FF]{2}|\U0001F310)', decoded)
    if flag_match:
        flag = flag_match.group(1)
        if flag in COUNTRY_RU:
            return flag, COUNTRY_RU[flag]

    # 2. Ищем английское название → подбираем флаг через CODE_TO_FLAG
    decoded_lower = decoded.lower()
    for eng, rus in COUNTRY_NAMES_EN.items():
        if eng in decoded_lower:
            for code, name in COUNTRY_RU.items():
                if name == rus and code in CODE_TO_FLAG:
                    return CODE_TO_FLAG[code], rus
            return "🌐", rus

    return "🌐", "Сервер"

def rename_key(line: str, label: str) -> str:
    """
    Переименовывает один ключ.
    Приоритетные источники  → label = 'WiFi'  → 🇩🇪 Германия - WiFi
    SNI/CIDR источники      → label = 'LTE'   → 🇩🇪 Германия - LTE
    Цифры не добавляются — серверы одной страны называются одинаково.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return line

    for proto in ["vless://", "vmess://", "trojan://", "ss://", "ssr://", "hysteria2://", "tuic://"]:
        if line.lower().startswith(proto):
            break
    else:
        return line  # не ключ — оставляем как есть

    try:
        parsed = urlparse(line)
        flag, country = get_flag_and_country(parsed.fragment)
        new_name = f"{flag} {country} - {label}"
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, parsed.query, quote(new_name)
        ))
    except Exception:
        return line  # если парсинг упал — возвращаем оригинал

def rename_block(configs: list, label: str) -> list:
    """Переименовывает список ключей одним вызовом."""
    return [rename_key(line, label) for line in configs]

# ══════════════════════════════════════════════════════════════════
#  ФИЛЬТРЫ (без изменений)
# ══════════════════════════════════════════════════════════════════

def is_cloudflare(config):
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def is_bad_sni_cidr(config):
    config_lower = config.lower()
    if 'anycast-ip' in config_lower: return True
    if any(p in config_lower for p in ['ee-', 'estonia', 'ee:', 'tallinn', '🇪🇪']): return 'EE_LAST'
    return False

def extract_country(config):
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/', '🇩🇪'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/', '🇳🇱'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/', '🇫🇷'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/', '🇷🇺'],
        'FI': ['fi-', 'finland', 'fi:', 'helsinki', '🇫🇮'],
        'US': ['us-', 'usa', 'us:', 'newyork', '🇺🇸'],
        'SG': ['sg-', 'singapore', 'sg:', '🇸🇬'],
        'GB': ['gb-', 'uk', 'gb:', 'london', '🇬🇧'],
        'CA': ['ca-', 'canada', 'ca:', 'toronto', '🇨🇦'],
        'SE': ['se-', 'sweden', 'se:', 'stockholm', '🇸🇪'],
        'NO': ['no-', 'norway', 'no:', 'oslo', '🇳🇴'],
        'DK': ['dk-', 'denmark', 'dk:', 'copenhagen', '🇩🇰'],
        'CH': ['ch-', 'switzerland', 'ch:', 'zurich', '🇨🇭'],
        'AT': ['at-', 'austria', 'at:', 'vienna', '🇦🇹'],
        'BE': ['be-', 'belgium', 'be:', 'brussels', '🇧🇪'],
        'IE': ['ie-', 'ireland', 'ie:', 'dublin', '🇮🇪'],
        'PL': ['pl-', 'poland', 'pl:', 'warsaw', '🇵🇱'],
        'CZ': ['cz-', 'czech', 'cz:', 'prague', '🇨🇿'],
        'IT': ['it-', 'italy', 'it:', 'rome', 'milan', '🇮🇹'],
        'ES': ['es-', 'spain', 'es:', 'madrid', '🇪🇸'],
        'AU': ['au-', 'australia', 'au:', 'sydney', '🇦🇺'],
        'JP': ['jp-', 'japan', 'jp:', 'tokyo', '🇯🇵']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

# ══════════════════════════════════════════════════════════════════
#  ОСНОВНОЙ СКРИПТ
# ══════════════════════════════════════════════════════════════════

print("🚀 SPECTER VPN Тариф 20 — 4/4/4/3 + 16 стран + МАКС SNI/CIDR!")

# ── 1. ФИКСИРОВАННЫЕ БЛОКИ: 4DE / 4NL / 4FR / 3RU ───────────────
target_blocks = {'DE': 4, 'NL': 4, 'FR': 4, 'RU': 3}
collected_blocks = {country: [] for country in target_blocks}

print("\n📥 ФИКСИРОВАННЫЕ БЛОКИ 4/4/4/3:")
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

# Переименовываем блоки → WiFi
for country in collected_blocks:
    collected_blocks[country] = rename_block(collected_blocks[country], "WiFi")

# ── 2. 16 УНИКАЛЬНЫХ СЛУЧАЙНЫХ СТРАН ─────────────────────────────
print("\n📥 16 УНИКАЛЬНЫХ СТРАН (по 1 с каждой):")
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

# РОВНО 16 случайных стран
random_countries_list = list(random_countries.keys())
random.shuffle(random_countries_list)
selected_random = random_countries_list[:16]

# Переименовываем случайные страны → WiFi
for country in selected_random:
    random_countries[country] = rename_block(random_countries[country][:1], "WiFi")

# ── 3. SNI/CIDR → LTE ────────────────────────────────────────────
print("\n📥 SNI/CIDR (20+ ключей):")
sni_cidr_configs = []
sni_cidr_ee = []

for i, source in enumerate(SNI_CIDR_SOURCES):
    source_name = source.split('/')[-1]
    print(f"  {i+1}. {source_name}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]

        if 'SNI-RU-all' in source_name:
            lines = lines[2:]

        filtered_lines = []
        for line in lines:
            bad_result = is_bad_sni_cidr(line)
            if not is_cloudflare(line):
                if bad_result == 'EE_LAST':
                    sni_cidr_ee.append(line)
                elif not bad_result:
                    filtered_lines.append(line)

        if 'CIDR' in source_name:
            selected = filtered_lines[:10]
        else:
            selected = filtered_lines

        sni_cidr_configs.extend(selected)
        print(f"     ✅ +{len(selected)} ключей")
    except:
        print(f"     ❌")

print(f"\n📊 SNI/CIDR: {len(sni_cidr_configs)} норм + {len(sni_cidr_ee)} 🇪🇪")

# Переименовываем SNI/CIDR → LTE
sni_cidr_configs = rename_block(sni_cidr_configs, "LTE")
sni_cidr_ee      = rename_block(sni_cidr_ee,      "LTE")

# ── 4. ФИНАЛЬНАЯ СБОРКА ───────────────────────────────────────────
final_configs = []

print("\n🎯 СОБИРАЕМ ТАРИФ 20:")

for country in ['DE', 'NL', 'FR', 'RU']:
    block = collected_blocks[country]
    final_configs.extend(block)
    print(f"✅ БЛОК {country}: {len(block)}")

for country in selected_random:
    block = random_countries[country][:1]
    final_configs.extend(block)
    print(f"✅ СЛУЧАЙНАЯ {country}: 1")

final_configs.extend(sni_cidr_configs[:25])
final_configs.extend(sni_cidr_ee[:3])

# Ровно 60 серверов
final_configs = final_configs[:60]

content = HEADER_TARIF20 + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print("📋 4DE + 4NL + 4FR + 3RU + 16 случайных + 25 SNI/CIDR + 3 EE = 60")

# ── 5. ЗАГРУЗКА В S3 ──────────────────────────────────────────────
try:
    s3_client.put_object(
        Bucket='tariff20',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ТАРИФ 20 ЗАГРУЖЕН!")
    print("🔗 Happ: https://storage.yandexcloud.net/tariff20/отобранные.txt")
    print("🎉 НАЗВАНИЕ: SPECTER VPN Tariff 20!")
except Exception as e:
    print(f"❌ {e}")

print("\n🎉 ТАРИФ 20 — 4/4/4/3 + 16 стран + МАКС SNI/CIDR готов!")
