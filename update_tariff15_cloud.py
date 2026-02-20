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

# ===== ПРИОРИТЕТНЫЕ ИСТОЧНИКИ (первые 4 — без SNI/CIDR) =====
PRIORITY_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
]

# ===== SNI/CIDR ИСТОЧНИКИ (всегда В КОНЕЦ) =====
SNI_CIDR_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'
]

# ===== ТВОИ ТОЧНЫЕ 2 СТРОЧКИ =====
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
#profile-update-interval: 12"""

def is_cloudflare(config):
    """Исключаем Cloudflare"""
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def extract_country(config):
    """СТРОГОЕ определение приоритетных стран"""
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/', '🇩🇪', 'germani'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/', '🇳🇱', 'niderland'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/', '🇫🇷', 'french'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/', '🇷🇺', 'russian']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

print("🚀 SPECTER VPN — ПРИОРИТЕТ DE/NL/FR/RU → ДРУГИЕ → SNI/CIDR")

# ===== 1. ИЗ КАЖДОГО ПРИОРИТЕТНОГО ИСТОЧНИКА БЕРЁМ ПО 1 ДЕ/НЛ/ФР/РУ =====
priority_configs = defaultdict(list)  # DE: [ключ1, ключ2, ключ3, ...]
sni_cidr_configs = []

print("\n📥 ПРИОРИТЕТНЫЕ ИСТОЧНИКИ (DE/NL/FR/RU по 1 с каждого):")
for i, source in enumerate(PRIORITY_SOURCES):
    print(f"  {i+1}. {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [line.strip() for line in resp.text.splitlines()[3:] if line.strip()]
        valid_lines = [line for line in lines if not is_cloudflare(line)]
        
        # ИЗ КАЖДОГО ИСТОЧНИКА БЕРЁМ ПО 1 ДЕ, 1 НЛ, 1 ФР, 1 РУ
        for country in ['DE', 'NL', 'FR', 'RU']:
            country_lines = [line for line in valid_lines if extract_country(line) == country]
            if country_lines:
                key = random.choice(country_lines)
                priority_configs[country].append(key)
                print(f"     ✅ {country}: 1 ключ")
        
    except Exception as e:
        print(f"     ❌ {e}")

# ===== 2. SNI/CIDR ВСЕГДА В КОНЕЦ =====
print("\n📥 SNI/CIDR ИСТОЧНИКИ (ВСЕГДА В КОНЕЦ):")
for i, source in enumerate(SNI_CIDR_SOURCES):
    print(f"  {i+1}. {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [line.strip() for line in resp.text.splitlines()[3:] if line.strip()]
        valid_lines = [line for line in lines if not is_cloudflare(line)]
        sni_cidr_configs.extend(valid_lines[:2])  # По 2 с каждого
        print(f"     ✅ +{min(2, len(valid_lines))} ключей")
    except:
        print(f"     ❌ Ошибка")

print(f"\n📊 Приоритетные блоки:")
for country, keys in priority_configs.items():
    print(f"  {country}: {len(keys)} ключей")

# ===== 3. СТРОГИЙ ПОРЯДОК БЛОКОВ =====
country_order = ['DE', 'NL', 'FR', 'RU']
final_configs = []

print("\n🎯 ФОРМИРУЕМ БЛОКИ:")
for country in country_order:
    if country in priority_configs:
        block = priority_configs[country]
        final_configs.extend(block)
        print(f"✅ БЛОК {country}: {len(block)} ключей")

# ===== 4. ДОБИРАЕМ ДО 30 ЛЮБЫМИ СТРАНАМИ =====
remaining_configs = []
all_keys = []
for source_configs in PRIORITY_SOURCES + SNI_CIDR_SOURCES:
    resp = requests.get(source_configs, timeout=10)
    lines = [line.strip() for line in resp.text.splitlines()[3:] if line.strip()]
    valid_lines = [line for line in lines if not is_cloudflare(line)]
    remaining_configs.extend(valid_lines)

# Исключаем уже использованные
used_keys = set(final_configs)
for key in remaining_configs:
    if key not in used_keys and len(final_configs) < 30:
        final_configs.append(key)

# ===== 5. SNI/CIDR СТРОГО В КОНЕЦ =====
final_configs = final_configs[:30] + sni_cidr_configs
content = HEADER + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГОВЫЙ СПИСОК: {len(final_configs)} ключей")
print("📋 ПОРЯДОК: DE→NL→FR→RU→ДРУГИЕ→SNI/CIDR")

# ===== ЗАГРУЖАЕМ =====
try:
    s3_client.put_object(
        Bucket='tariff15',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ЗАГРУЖЕНО В ЯНДЕКС CLOUD!")
    print("🔗 ПОСТОЯННАЯ ССЫЛКА ДЛЯ HAPP:")
    print("https://storage.yandexcloud.net/tariff15/отобранные.txt")
except Exception as e:
    print(f"❌ {e}")

print("\n🎉 SPECTER VPN — СТРОГИЕ БЛОКИ готов!")
