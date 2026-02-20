import boto3
import requests
import random
import re
import os
from collections import defaultdict

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

# ===== SPECTER VPN НАЗВАНИЕ ДЛЯ HAPP =====
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
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
        'GB': ['gb-', 'uk', 'gb:', 'london', '🇬🇧']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

print("🚀 SPECTER VPN — 23 обычных + 12 SNI/CIDR в конце!")

# ===== 1. ПРИОРИТЕТНЫЕ БЛОКИ DE/NL/FR/RU (макс 3 на страну) =====
priority_blocks = {'DE': [], 'NL': [], 'FR': [], 'RU': []}

print("\n📥 ПРИОРИТЕТНЫЕ ИСТОЧНИКИ (DE/NL/FR/RU):")
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
                        print(f"     ✅ {country}: +1 (всего {len(priority_blocks[country])})")
    except:
        print(f"     ❌")

# ===== 2. МАКСИМУМ SNI/CIDR (ПО 4 С КАЖДОГО = 12 ШТУК!) =====
sni_cidr_configs = []
print("\n📥 SNI/CIDR (ПО 4 С КАЖДОГО = 12 ШТУК):")
for i, source in enumerate(SNI_CIDR_SOURCES):
    source_name = source.split('/')[-1]
    print(f"  {i+1}. {source_name}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        valid_lines = [l for l in lines if not is_cloudflare(l)]
        
        selected = valid_lines[:4]
        sni_cidr_configs.extend(selected)
        print(f"     ✅ +{len(selected)} SNI/CIDR ключей")
    except:
        print(f"     ❌")

print(f"\n📊 SNI/CIDR всего: {len(sni_cidr_configs)} ключей ✓")

# ===== 3. ДОБИРАЕМ РАЗНЫЕ СТРАНЫ (макс 2 на страну) =====
print("\n📥 ДОБОР РАЗНЫХ СТРАН (1-2 сервера/страна):")
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

# ===== 4. ФИНАЛЬНАЯ СОБИРКА =====
country_order = ['DE', 'NL', 'FR', 'RU']
final_configs = []

print("\n🎯 СОБИРАЕМ ИДЕАЛЬНЫЙ СПИСОК:")
for country in country_order:
    block = priority_blocks[country]
    if block:
        final_configs.extend(block)
        print(f"✅ БЛОК {country}: {len(block)} серверов")

other_order = sorted(other_countries.keys())
for country in other_order:
    block = other_countries[country][:2]
    if block:
        final_configs.extend(block)
        print(f"✅ {country}: {len(block)} серверов")

final_configs = final_configs[:23]
final_configs.extend(sni_cidr_configs[:12])
final_configs = final_configs[:35]

content = HEADER + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print(f"📋 23 обычных + {len(sni_cidr_configs[:12])} SNI/CIDR")

# ===== ЗАГРУЗКА =====
try:
    s3_client.put_object(
        Bucket='tariff15',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ЗАГРУЖЕНО В ЯНДЕКС CLOUD!")
    print("🔗 Happ: https://storage.yandexcloud.net/tariff15/отобранные.txt")
    print("🎉 НАЗВАНИЕ В HAPP: SPECTER VPN!")
except Exception as e:
    print(f"❌ {e}")

print("\n🎉 SPECTER VPN — ИДЕАЛЬНЫЙ СПИСОК готов!")
