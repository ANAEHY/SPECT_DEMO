import boto3
import requests
import random
import re
import os
from collections import defaultdict

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

# ===== НАЗВАНИЕ "SPECTER VPN Tariff 10" =====
HEADER_TARIF10 = """#profile-title: base64:8J+ktCBTUEVDVEVSIFZQTg== 
#profile-update-interval: 12"""

def is_cloudflare(config):
    """Исключаем Cloudflare"""
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def extract_country(config):
    """Расширенная сортировка стран"""
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

print("🚀 SPECTER VPN Тариф 10 — 3DE/3NL/3FR/2RU + 6 случайных!")

# ===== 1. ФИКСИРОВАННЫЕ БЛОКИ: 3/3/3/2 =====
target_blocks = {
    'DE': 3,  # 🎯 3 Германии
    'NL': 3,  # 🎯 3 Нидерланды
    'FR': 3,  # 🎯 3 Франции  
    'RU': 2   # 🎯 1-2 России
}

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
                available = len(country_lines)
                needed = target_count - len(collected_blocks[country])
                
                if country_lines:
                    # Берём нужное количество без повторов
                    selected = random.sample(country_lines, min(needed, available))
                    for key in selected:
                        if key not in collected_blocks[country]:
                            collected_blocks[country].append(key)
                    print(f"     ✅ {country}: +{len(selected)} (всего {len(collected_blocks[country])}/{target_count})")
    except:
        print(f"     ❌")

# ===== 2. 6 СЛУЧАЙНЫХ РАЗНЫХ СТРАН =====
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
                len(random_countries[country]) < 1):  # ПО 1 С КАЖДОЙ!
                random_countries[country].append(line)
    except:
        pass

# Берём РОВНО 6 случайных стран
random_countries_list = list(random_countries.keys())
random.shuffle(random_countries_list)
selected_random = random_countries_list[:6]

# ===== 3. ФИНАЛЬНАЯ СОБИРКА =====
final_configs = []

print("\n🎯 СОБИРАЕМ ТАРИФ 10 (17 серверов):")
# Фиксированные блоки
for country in ['DE', 'NL', 'FR', 'RU']:
    block = collected_blocks[country]
    final_configs.extend(block)
    print(f"✅ БЛОК {country}: {len(block)} серверов")

# 6 случайных стран
for country in selected_random:
    block = random_countries[country][:1]  # РОВНО 1!
    final_configs.extend(block)
    print(f"✅ СЛУЧАЙНАЯ {country}: 1 сервер")

# Ровно 17 серверов
final_configs = final_configs[:17]

content = HEADER_TARIF10 + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print("📋 3DE + 3NL + 3FR + 2RU + 6 случайных = 17")

# ===== ЗАГРУЗКА В tariff10 =====
try:
    s3_client.put_object(
        Bucket='tariff10',  # ← НОВЫЙ БАКЕТ!
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
