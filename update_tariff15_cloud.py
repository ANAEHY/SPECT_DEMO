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

# ===== ТВОИ 7 ИСТОЧНИКОВ =====
SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
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
    """СТРОГОЕ определение страны"""
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/', '🇩🇪'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/', '🇫🇷'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/', '🇳🇱'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/', '🇷🇺'],
        'US': ['us-', 'usa', 'us:', 'newyork', '🇺🇸'],
        'SG': ['sg-', 'singapore', 'sg:', '🇸🇬'],
        'GB': ['gb-', 'uk', 'gb:', 'london', '🇬🇧']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

print("🚀 SPECTER VPN — БЛОКИ ПО СТРАНАМ (SNI/CIDR В КОНЦЕ)")

# ===== СОБИРАЕМ КЛЮЧИ ПО ИСТОЧНИКАМ =====
all_configs_by_source = []
for i, source in enumerate(SOURCES):
    print(f"\n📥 {i+1}/7 {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [line.strip() for line in resp.text.splitlines()[3:] if line.strip()]
        valid_lines = [line for line in lines if not is_cloudflare(line)]
        
        # СТРОГО 5 ИЗ КАЖДОГО
        selected = random.sample(valid_lines, min(5, len(valid_lines)))
        all_configs_by_source.append(selected)
        print(f"   ✅ {len(selected)} ключей")
    except:
        print(f"   ❌ Ошибка")

# ===== ГРУППИРУЕМ ПО СТРАНАМ (БЛОКИ) =====
country_blocks = defaultdict(list)
sni_cidr_keys = []

for source_configs in all_configs_by_source:
    for config in source_configs:
        country = extract_country(config)
        source_name = next((s.split('/')[-1] for s in SOURCES), '')
        
        # SNI/CIDR ОТДЕЛЬНО В КОНЕЦ
        if 'SNI' in source_name or 'CIDR' in source_name:
            sni_cidr_keys.append(config)
        else:
            country_blocks[country].append(config)

print(f"\n📊 Блоки стран: {dict((k, len(v)) for k, v in country_blocks.items())}")
print(f"📋 SNI/CIDR: {len(sni_cidr_keys)} ключей")

# ===== СТРОГИЙ ПОРЯДОК: DE→FR→NL→RU→остальные =====
country_order = ['DE', 'FR', 'NL', 'RU', 'US', 'SG', 'GB', 'OTHER']
final_configs = []

for country in country_order:
    if country in country_blocks:
        # БЛOK СТРАНЫ — все ключи подряд
        final_configs.extend(country_blocks[country])
        print(f"✅ Блок {country}: {len(country_blocks[country])} ключей")

# ДО 35 КЛЮЧЕЙ + SNI/CIDR В КОНЕЦ
final_configs = final_configs[:33] + sni_cidr_keys[:2]
content = HEADER + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} ключей")
print("📝 Порядок: DE→FR→NL→RU→US→SNI/CIDR")

# ===== ЗАГРУЖАЕМ В ЯНДЕКС CLOUD =====
try:
    s3_client.put_object(
        Bucket='tariff15',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("\n✅ ✅ ✅ ЗАГРУЖЕНО!")
    print("🔗 Ссылка для Happ:")
    print("https://storage.yandexcloud.net/tariff15/отобранные.txt")
except Exception as e:
    print(f"❌ Загрузка: {e}")

print("\n🎉 SPECTER VPN — БЛОКИ ПО СТРАНАМ готов!")
