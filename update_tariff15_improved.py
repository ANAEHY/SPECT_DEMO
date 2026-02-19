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

KEYS_PER_SOURCE = [3, 5, 3, 2, 2, 2, 3]
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
#profile-update-interval: 1"""

def extract_country(config):
    """Извлекает страну из vless/ss ссылки"""
    # Паттерны стран в конфигах
    country_patterns = {
        'DE': ['de-', 'germany', 'de:', 'berlin', 'frankfurt'],
        'NL': ['nl-', 'netherlands', 'nl:', 'amsterdam', 'rotterdam'],
        'US': ['us-', 'usa', 'us:', 'newyork', 'losangeles'],
        'SG': ['sg-', 'singapore', 'sg:'],
        'GB': ['gb-', 'uk', 'gb:', 'london'],
        'FR': ['fr-', 'france', 'fr:', 'paris'],
        'CA': ['ca-', 'canada', 'ca:', 'toronto']
    }
    
    config_lower = config.lower()
    for country, patterns in country_patterns.items():
        for pattern in patterns:
            if pattern in config_lower:
                return country
    return 'RU'  # По умолчанию Россия

print("🌍 Загружаем и сортируем по странам...")

all_configs = []
country_stats = defaultdict(int)

# Тянем ключи, ПРОПУСКАЯ первые 3 строки
for i, source in enumerate(SOURCES):
    print(f"\n📥 {i+1}. {source.split('/')[-1]}")
    try:
        response = requests.get(source, timeout=10)
        if response.status_code == 200:
            # Пропускаем первые 3 строки (инфо)
            lines = response.text.splitlines()[3:]
            lines = [line.strip() for line in lines if line.strip()]
            print(f"   → {len(lines)} ключей (после пропуска инфо)")
            
            if len(lines) >= KEYS_PER_SOURCE[i]:
                selected = random.sample(lines, KEYS_PER_SOURCE[i])
            else:
                selected = lines
                print(f"   ⚠️ Берём все {len(selected)}")
            
            for config in selected:
                country = extract_country(config)
                country_stats[country] += 1
                all_configs.append((config, country))
                
    except Exception as e:
        print(f"   ❌ {e}")

print(f"\n📊 Страны: {dict(country_stats)}")
print(f"🎲 Всего ключей: {len(all_configs)}")

# ✅ Гарантируем Германию + Нидерланды
de_configs = [cfg for cfg, country in all_configs if country == 'DE']
nl_configs = [cfg for cfg, country in all_configs if country == 'NL']

final_configs = []

# Обязательно берём DE + NL
if de_configs:
    final_configs.append(random.choice(de_configs))
    print("✅ Германия добавлена")
if nl_configs:
    final_configs.append(random.choice(nl_configs))
    print("✅ Нидерланды добавлены")

# Остальные ключи по алфавиту стран
remaining = [(cfg, country) for cfg, country in all_configs if cfg not in final_configs]
remaining.sort(key=lambda x: x[1])  # Сортировка по стране

final_configs.extend([cfg for cfg, _ in remaining[:13]])  # 15 всего

# Финальный файл
keys_content = '\n'.join(final_configs)
final_content = HEADER + '\n' + keys_content

with open('tariff15.txt', 'w') as f:
    f.write(final_content)

print(f"\n✅ tariff15.txt готов! {len(final_configs)} стран:")
print("   DE, NL + остальные по алфавиту")
print("📋 Raw: https://raw.githubusercontent.com/ANAEHY/SPECT_DEMO/main/tariff15.txt")
