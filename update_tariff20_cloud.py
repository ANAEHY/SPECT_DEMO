import boto3
import requests
import random
import re
import os
from collections import defaultdict

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
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',  # SNI
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',                    # CIDR checked (10)
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU.txt',                           # CIDR all (10)  
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'                         # Весь SNI кроме 2 строк
]

HEADER_TARIF20 = """#profile-title: base64:8J+ktCBTUEVDVEVSIFRhcmlmIDIw
#profile-update-interval: 12"""

def is_cloudflare(config):
    """Исключаем Cloudflare"""
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def is_bad_sni_cidr(config):
    """Исключаем anycast-ip + Эстония в конец"""
    config_lower = config.lower()
    if 'anycast-ip' in config_lower: return True
    if any(p in config_lower for p in ['ee-', 'estonia', 'ee:', 'tallinn', '🇪🇪']): return 'EE_LAST'
    return False

def extract_country(config):
    """Расширенная сортировка 20+ стран"""
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
        'CZ': ['cz-', 'czech', 'cz:', 'prague', '🇨🇿']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

print("🚀 SPECTER VPN Тариф 20 — 4/4/4/3 + 16 стран + МАКС SNI/CIDR!")

# ===== 1. ФИКСИРОВАННЫЕ БЛОКИ: 4DE/4NL/4FR/3RU =====
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

# ===== 2. 16 УНИКАЛЬНЫХ СЛУЧАЙНЫХ СТРАН =====
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
                len(random_countries[country]) < 1):  # СТРОГО 1 С КАЖДОЙ!
                random_countries[country].append(line)
    except:
        pass

# РОВНО 16 случайных стран
random_countries_list = list(random_countries.keys())
random.shuffle(random_countries_list)
selected_random = random_countries_list[:16]

# ===== 3. МАКСИМУМ SNI/CIDR =====
print("\n📥 SNI/CIDR (20+ ключей):")
sni_cidr_configs = []
sni_cidr_ee = []

for i, source in enumerate(SNI_CIDR_SOURCES):
    source_name = source.split('/')[-1]
    print(f"  {i+1}. {source_name}")
    try:
        resp = requests.get(source, timeout=10)
        lines = [l.strip() for l in resp.text.splitlines()[3:] if l.strip()]
        
        if 'SNI-RU-all' in source_name:  # ВЕСЬ SNI кроме первых 2 строк
            lines = lines[2:]  # Пропускаем информ. строки
        
        filtered_lines = []
        for line in lines:
            bad_result = is_bad_sni_cidr(line)
            if not is_cloudflare(line):
                if bad_result == 'EE_LAST':
                    sni_cidr_ee.append(line)
                elif not bad_result:
                    filtered_lines.append(line)
        
        # По 10 с CIDR + весь SNI
        if 'CIDR' in source_name:
            selected = filtered_lines[:10]
        else:
            selected = filtered_lines  # Весь SNI
        
        sni_cidr_configs.extend(selected)
        print(f"     ✅ +{len(selected)} ключей")
    except:
        print(f"     ❌")

print(f"\n📊 SNI/CIDR: {len(sni_cidr_configs)} норм + {len(sni_cidr_ee)} 🇪🇪")

# ===== 4. ФИНАЛЬНАЯ СОБИРКА (50+ серверов) =====
final_configs = []

print("\n🎯 СОБИРАЕМ ТАРИФ 20:")
# Фиксированные блоки 4/4/4/3 = 15
for country in ['DE', 'NL', 'FR', 'RU']:
    block = collected_blocks[country]
    final_configs.extend(block)
    print(f"✅ БЛОК {country}: {len(block)}")

# 16 случайных стран = 16
for country in selected_random:
    block = random_countries[country][:1]
    final_configs.extend(block)
    print(f"✅ СЛУЧАЙНАЯ {country}: 1")

# SNI/CIDR блок
final_configs.extend(sni_cidr_configs[:25])
final_configs.extend(sni_cidr_ee[:3])

# Ровно 60 серверов
final_configs = final_configs[:60]

content = HEADER_TARIF20 + '\n' + '\n'.join(final_configs)

print(f"\n🎯 ИТОГО: {len(final_configs)} серверов")
print("📋 4DE + 4NL + 4FR + 3RU + 16 случайных + 25 SNI/CIDR + 3 EE = 60")

# ===== ЗАГРУЗКА В tariff20 =====
try:
    s3_client.put_object(
        Bucket='tariff20',  # НОВЫЙ бакет!
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
