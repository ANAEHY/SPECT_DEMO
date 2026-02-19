import requests
import random
import re
from collections import defaultdict

SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'
]

HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
#profile-update-interval: 1"""

def is_cloudflare_ip(config):
    """Исключаем Cloudflare IP"""
    cf_patterns = ['cloudflare', 'cf-ip', '1.1.1.1', '1.0.0.1', '104.', '172.67.', '141.193.']
    config_lower = config.lower()
    return any(pattern in config_lower for pattern in cf_patterns)

def extract_country(config):
    """Извлекает страну из конфига"""
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
        for pat in pats:
            if pat in config_lower:
                return country
    return 'OTHER'

print("🚀 Тариф 15 PRO: DE+FR+NL x3 + RU 1-2 + SNI/CIDR в конце")

# Собираем по 5 из каждого источника
all_configs_by_source = []
country_stats = defaultdict(list)

for i, source in enumerate(SOURCES):
    print(f"\n📥 {i+1}. {source.split('/')[-1]}")
    try:
        response = requests.get(source, timeout=10)
        if response.status_code == 200:
            # Пропускаем первые 3 строки
            lines = [line.strip() for line in response.text.splitlines()[3:] if line.strip()]
            
            # Фильтр Cloudflare + выборка по странам
            valid_lines = []
            for line in lines:
                if not is_cloudflare_ip(line):
                    valid_lines.append(line)
            
            print(f"   → {len(lines)} всего → {len(valid_lines)} без CF")
            
            if len(valid_lines) >= 5:
                selected = random.sample(valid_lines, 5)
            else:
                selected = valid_lines[:5]
            
            source_configs = []
            for config in selected:
                country = extract_country(config)
                country_stats[country].append(config)
                source_configs.append((config, country, source.split('/')[-1]))
            
            all_configs_by_source.append(source_configs)
            
    except Exception as e:
        print(f"   ❌ {e}")

print(f"\n📊 Доступные страны: {list(country_stats.keys())}")

# Формируем финальный список (35 ключей всего)
final_configs = []

# ✅ 1. Обязательно 3 DE, 3 FR, 3 NL из КАЖДОГО источника где возможно
priority_countries = ['DE', 'FR', 'NL']
for source_configs in all_configs_by_source:
    for country in priority_countries:
        country_configs = [cfg for cfg, cnt, src in source_configs if cnt == country]
        if country_configs and len(final_configs) < 30:
            final_configs.append(random.choice(country_configs))
            print(f"✅ {country} из {source_configs[0][2]}")

# ✅ 2. 1-2 RU IP в середину
ru_configs = []
for source_configs in all_configs_by_source:
    ru_in_source = [cfg for cfg, cnt, src in source_configs if cnt == 'RU']
    ru_configs.extend(ru_in_source)

if ru_configs:
    ru_selected = random.sample(ru_configs, min(2, len(ru_configs)))
    final_configs.extend(ru_selected[:2])
    print(f"✅ RU IP: {len(ru_selected)}")

# ✅ 3. Остальные случайные до 30 ключей
remaining_configs = []
for source_configs in all_configs_by_source:
    for cfg, cnt, src in source_configs:
        if cfg not in final_configs and len(final_configs) < 30:
            remaining_configs.append(cfg)

random.shuffle(remaining_configs)
final_configs.extend(remaining_configs[:30 - len(final_configs)])

print(f"\n🎯 Финальный список: {len(final_configs)} ключей")

# ✅ 4. SNI + CIDR в КОНЕЦ
sni_configs = []
cidr_configs = []
for source_configs in all_configs_by_source:
    for cfg, cnt, src in source_configs:
        if 'SNI' in src and cfg in final_configs:
            sni_configs.append(cfg)
        if 'CIDR' in src and cfg in final_configs:
            cidr_configs.append(cfg)

# Убираем SNI/CIDR из основного списка, ставим в конец
final_main = [cfg for cfg in final_configs if cfg not in sni_configs + cidr_configs]
final_configs = final_main + sni_configs + cidr_configs

print(f"📋 Итого: {len(final_main)} основных + {len(sni_configs)} SNI + {len(cidr_configs)} CIDR")

# Сохраняем
keys_content = '\n'.join(final_configs)
final_content = HEADER + '\n' + keys_content

with open('tariff15.txt', 'w') as f:
    f.write(final_content)

print("\n✅ tariff15.txt PRO готов!")
print("🌟 3DE + 3FR + 3NL из каждого + 1-2 RU + SNI/CIDR в конце")
print("📋 Raw: https://raw.githubusercontent.com/ANAEHY/SPECT_DEMO/main/tariff15.txt")
