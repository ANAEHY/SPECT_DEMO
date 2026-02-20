import boto3
import requests
import random
import re
import os
from collections import defaultdict

# ===== ЯНДЕКС CLOUD S3 =====
ACCESS_KEY = os.getenv('YANDEX_ACCESS_KEY')
SECRET_KEY = os.getenv('YANDEX_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    print("❌ Ошибка: Добавь YANDEX_ACCESS_KEY и YANDEX_SECRET_KEY в GitHub Secrets!")
    exit(1)

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='ru-central1'
)

# ===== ИСТОЧНИКИ VPN КЛЮЧЕЙ =====
SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'
]

HEADER = """#profile-title: SPECTER VPN CLOUD
#profile-update-interval: 6
# Автообновление каждые 6 часов! Работает под РКИ
"""

def is_cloudflare(config):
    """Исключаем Cloudflare IP"""
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '1.0.0.1', '104.', '172.67.', '141.193.']
    return any(pattern in config.lower() for pattern in cf_patterns)

def extract_country(config):
    """Определяем страну по ключу"""
    patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt', 'de/'],
        'FR': ['fr-', 'france', 'fr:', 'paris', 'fr/'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam', 'nl/'],
        'RU': ['ru-', 'russia', 'ru:', 'moscow', 'spb', 'ru/'],
        'US': ['us-', 'usa', 'us:', 'newyork'],
        'SG': ['sg-', 'singapore', 'sg:'],
        'GB': ['gb-', 'uk', 'gb:', 'london']
    }
    config_lower = config.lower()
    for country, pats in patterns.items():
        if any(pat in config_lower for pat in pats):
            return country
    return 'OTHER'

print("🚀 SPECTER VPN CLOUD — 35 ключей (DE+FR+NL+RU)")

# ===== СОБИРАЕМ КЛЮЧИ =====
all_configs = []
country_stats = defaultdict(list)

for i, source in enumerate(SOURCES):
    print(f"📥 {i+1}/7 {source.split('/')[-1]}")
    try:
        resp = requests.get(source, timeout=10)
        if resp.status_code == 200:
            # Пропускаем первые 3 строки (инфо)
            lines = [line.strip() for line in resp.text.splitlines()[3:] if line.strip()]
            
            # Фильтр Cloudflare
            valid_lines = [line for line in lines if not is_cloudflare(line)]
            print(f"   → {len(lines)} всего → {len(valid_lines)} без CF")
            
            # Берём РАНДОМНО 5 из каждого
            if len(valid_lines) >= 5:
                selected = random.sample(valid_lines, 5)
            else:
                selected = valid_lines[:5]
            
            # Статистика по странам
            for config in selected:
                country = extract_country(config)
                country_stats[country].append(config)
            
            all_configs.extend(selected)
            print(f"   ✅ +{len(selected)} ключей")
        else:
            print(f"   ❌ HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ {e}")

print(f"\n📊 Страны: {dict((k, len(v)) for k, v in country_stats.items())}")
print(f"🎯 Всего собрано: {len(all_configs)} ключей")

# ===== ФОРМИРУЕМ ФИНАЛЬНЫЙ СПИСОК =====
final_configs = all_configs[:35]  # Топ 35 лучших

# SNI и CIDR в конец
sni_cidr = []
main_configs = []
for config in final_configs:
    source_name = next((s.split('/')[-1] for s in SOURCES if s in config), '')
    if 'SNI' in source_name or 'CIDR' in source_name:
        sni_cidr.append(config)
    else:
        main_configs.append(config)

final_configs = main_configs + sni_cidr

content = HEADER + '\n' + '\n'.join(final_configs)
print(f"\n✅ Готово {len(final_configs)} ключей для Happ!")

# ===== ЗАГРУЖАЕМ В ЯНДЕКС CLOUD =====
try:
    s3_client.put_object(
        Bucket='tariff15',
        Key='отобранные.txt',
        Body=content,
        ContentType='text/plain; charset=utf-8'
    )
    print("✅ ✅ ✅ ЗАГРУЖЕНО В ЯНДЕКС CLOUD!")
    print("\n🔗 🎉 ПОСТОЯННАЯ ССЫЛКА ДЛЯ КЛИЕНТОВ:")
    print("https://storage.yandexcloud.net/tariff15/отобранные.txt")
    print("\n📱 Happ → Добавить подписку → вставь эту ссылку!")
    
except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    print("🔧 Проверь: 1) storage.admin роль 2) публичный доступ к бакету")

print("\n🎉 SPECTER VPN CLOUD готов к работе!")
