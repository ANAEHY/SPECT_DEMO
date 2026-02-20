import requests
import random

# 7 источников ключей (без изменений)
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

# ЧИСТЫЙ заголовок (как в тарифе 10)
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss
#profile-update-interval: 1"""

# Остальной код без изменений...
print("🧠 Загружаем 7 источников...")
all_keys = []

for i, source in enumerate(SOURCES):
    print(f"📥 {i+1}. {source.split('/')[-1]}")
    try:
        response = requests.get(source, timeout=10)
        if response.status_code == 200:
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]
            print(f"   → {len(lines)} ключей")
            
            if len(lines) >= KEYS_PER_SOURCE[i]:
                selected = random.sample(lines, KEYS_PER_SOURCE[i])
                all_keys.extend(selected)
            else:
                print(f"   ⚠️ Недостаточно, берём все {len(lines)}")
                all_keys.extend(lines)
        else:
            print(f"   ❌ Ошибка {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

print(f"\n🎲 Выбрано ключей: {len(all_keys)}")

final_keys = all_keys[:15]
keys_content = '\n'.join(final_keys)
final_content = HEADER + '\n' + keys_content

with open('tariff15.txt', 'w') as f:
    f.write(final_content)

print("✅ tariff15.txt готов! Чистый заголовок + 15 микс ключей")
