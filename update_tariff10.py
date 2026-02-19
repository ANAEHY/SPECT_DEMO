import requests
import random

SOURCE_RAW = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt'

# НЕИзмeнные первые 2 строки для Happ
HEADER = """#profile-title: base64:8J+ktCBTUEVDVEVSIFZQTiDwn5Ss
#profile-update-interval: 1"""

# Скачиваем ключи
print("Загружаем ключи...")
response = requests.get(SOURCE_RAW)
if response.status_code != 200:
    print(f"Ошибка: {response.status_code}")
    exit(1)

lines = [line.strip() for line in response.text.splitlines() if line.strip()]
print(f"Найдено ключей: {len(lines)}")

if len(lines) < 10:
    print("Недостаточно ключей!")
    exit(1)

# 10 случайных ключей
selected = random.sample(lines, 10)
keys_content = '\n'.join(selected)

# HEADER + ключи
final_content = HEADER + '\n' + keys_content

# Сохраняем
with open('tariff10.txt', 'w') as f:
    f.write(final_content)

print("✅ tariff10.txt обновлён!")
print("📋 Первые 2 строки + 10 новых ключей")
