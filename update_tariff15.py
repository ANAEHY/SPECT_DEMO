import requests
import random

# 7 источников ключей
SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS+All_RUS.txt',  # 3 SS
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',  # 5 VLESS
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',  # 3 mobile
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt',  # 2 Reality
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',  # 2 Reality
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',  # 2 CIDR
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt'  # 3 SNI
]

# Кол-во ключей из каждого источника
KEYS_PER_SOURCE = [3, 5, 3, 2, 2, 2, 3]  # Итого 20 строк

# Заголовок Happ
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFVQTiDwn5Ss 15 стран + белые
#profile-update-interval: 1"""

print("🧠 Загружаем 7 источников...")
all_keys = []

# Тянем ключи из всех источников
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
                print(f"   ⚠️ Недостаточно ключей, берём все {len(lines)}")
                all_keys.extend(lines)
        else:
            print(f"   ❌ Ошибка {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

print(f"\n🎲 Выбрано ключей: {len(all_keys)}")

# Берём первые 15 (если больше)
final_keys = all_keys[:15]
keys_content = '\n'.join(final_keys)

# HEADER + ключи
final_content = HEADER + '\n' + keys_content

# Сохраняем
with open('tariff15.txt', 'w') as f:
    f.write(final_content)

print("✅ tariff15.txt готов! 15 стран + белые списки")
print("📋 Raw: https://raw.githubusercontent.com/ANAEHY/SPECT_DEMO/main/tariff15.txt")
