import boto3
import requests
import random
import re
import os
from collections import defaultdict
from urllib.parse import urlparse, urlunparse, quote, unquote

# ===== ЯНДЕКС CLOUD S3 =====
ACCESS_KEY = os.getenv('YANDEX_ACCESS_KEY')
SECRET_KEY = os.getenv('YANDEX_SECRET_KEY')

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='ru-central1'
)

# ===== ПРИОРИТЕТНЫЕ ИСТОЧНИКИ (без SNI/CIDR) =====
PRIORITY_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
]

# ===== SNI/CIDR ИСТОЧНИКИ (12 ШТУК В КОНЕЦ!) =====
SNI_CIDR_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'
]

HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
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

def is_bad_sni_cidr(config):
    config_lower = config.lower()
    if 'anycast-ip' in config_lower:
        return True
    if any(p in config_lower for p in ['ee-', 'estonia', 'ee:', 'tallinn', '🇪🇪']):
        return 'EE_LAST'
    return False

def extract_country(config):
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/', '🇩🇪', 'germani'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/', '🇳🇱', 'niderland'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/', '🇫🇷', 'french'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/', '🇷🇺', 'russian'],
        'FI': ['fi-', 'finland', 'fi:', 'helsinki', '🇫🇮'],
        'US': ['us-', 'usa', 'us:', 'newyork', '🇺🇸'],
        'SG': ['sg-', 'singapore', 'sg:', '🇸🇬'],
        'GB': ['gb-', 'uk', 'gb:', 'london', '🇬🇧']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

# ══════════════════════════════════════════════════════════════════
#  ОСНОВНОЙ СКРИПТ
# ══════════════════════════════════════════════════════════════════

print("🚀 SPECTER VPN — ❌NO anycast-ip + 🇪🇪Эстония В КОНЕЦ!")

# ── 1. ПРИОРИТЕТНЫЕ БЛОКИ DE/NL/FR/RU ────────────────────────────
priority_blocks = {'DE': [], 'NL': [], 'FR': [], 'RU': []}

print("\n📥 ПРИОРИТЕТНЫЕ ИСТОЧНИКИ:")
for i, source in enumerate(PRIORITY_SOURCES):
    print(f"  {i+1}. {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        valid_lines = [l for l in lines if not is_cloudflare(l)]

        for country in ['DE', 'NL', 'FR', 'RU']:
            if len(priority_blocks[country]) < 3:
                country_lines = [l for l in valid_lines if extract_country(l) == country]
                if country_lines:
                    key = random.choice(country_lines)
                    if key not in priority_blocks[country]:
                        priority_blocks[country].append(key)
                        print(f"     ✅ {country}: +1")
    except:
        print(f"     ❌")

# Переименовываем → WiFi
for country in priority_blocks:
    priority_blocks[country] = rename_block(priority_blocks[country], "WiFi")

# ── 2. SNI/CIDR → LTE ────────────────────────────────────────────
sni_cidr_configs = []
sni_cidr_ee = []

print("\n📥 SNI/CIDR (❌NO anycast-ip + 🇪🇪В КОНЕЦ):")
for i, source in enumerate(SNI_CIDR_SOURCES):
    source_name = source.split('/')[-1]
    print(f"  {i+1}. {source_name}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]

        filtered_lines = []
        for line in lines:
            bad_result = is_bad_sni_cidr(line)
            if not is_cloudflare(line):
                if bad_result == 'EE_LAST':
                    sni_cidr_ee.append(line)
                elif not bad_result:
                    filtered_lines.append(line)

        selected = filtered_lines[:4]
        sni_cidr_configs.extend(selected)
        print(f"     ✅ +{len(selected)} нормальных (Эстония отдельно)")
    except:
        print(f"     ❌")

print(f"\n📊 SNI/CIDR: {len(sni_cidr_configs)} норм + {len(sni_cidr_ee)} 🇪🇪")

# Переименовываем → LTE
sni_cidr_configs = rename_block(sni_cidr_configs, "LTE")
sni_cidr_ee      = rename_block(sni_cidr_ee,      "LTE")

# ── 3. ДОБОР РАЗНЫХ СТРАН ─────────────────────────────────────────
print("\n📥 ДОБОР РАЗНЫХ СТРАН:")
other_countries = defaultdict(list)

for source in PRIORITY_SOURCES:
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        valid_lines = [l for l in lines if not is_cloudflare(l)]

        for line in valid_lines:
            country = extract_country(line)
            if country not in ['DE', 'NL', 'FR', 'RU'] and len(other_countries[country]) < 2:
                other_countries[country].append(line)
    except:
        pass

# Переименовываем → WiFi
for country in other_countries:
    other_countries[country] = rename_block(other_countries[country], "WiFi")

# ── 4. ФИНАЛЬНАЯ СБОРКА ───────────────────────────────────────────
final_configs = []

print("\n🎯 СОБИРАЕМ:")
for country in ['DE', 'NL', 'FR', 'RU']:
    block = priority_blocks[country]
    if block:
        final_configs.extend(block)
        print(f"✅ БЛОК {country}: {len(block)}")

for country in sorted(other_countries.keys()):
    block = other_countries[country][:2]
    if block:
        final_configs.extend(block)
        print(f"✅ {country}: {len(block)}")

final_configs = final_configs[:20]
final_configs.extend(sni_cidr_configs[:12])
final_configs.extend(sni_cidr_ee[:2])
final_configs = final_configs[:35]

content = HEADER + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print(f"📋 20 обычных + {len(sni_cidr_configs[:12])} SNI/CIDR + {len(sni_cidr_ee[:2])} 🇪🇪")

# ── 5. ЗАГРУЗКА В S3 ──────────────────────────────────────────────
try:
    s3_client.put_object(
        Bucket='tariff15',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ЗАГРУЖЕНО!")
    print("🔗 Happ: https://storage.yandexcloud.net/tariff15/отобранные.txt")
except Exception as e:
    print(f"❌ {e}")

print("\n🎉 ❌NO anycast-ip + 🇪🇪В КОНЕЦ — готов!")
