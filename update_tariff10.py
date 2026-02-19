import requests
import random

SOURCE_RAW = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt'

# Скачиваем все ключи
print("Загружаем ключи...")
response = requests.get(SOURCE_RAW)
if response.status_code != 200:
    print(f"Ошибка: {response.status_code}")
    exit(1)

lines = [line.strip() for line in response.text.splitlines() if line.strip()]
print(f"Найдено ключей: {len(lines)}")

# Выбираем случайные 10
if len(lines) < 10:
    print("Недостаточно ключей!")
    exit(1)

selected = random.sample(lines, 10)
new_content = '\n'.join(selected)

# Сохраняем в tariff10.txt
with open('tariff10.txt', 'w') as f:
    f.write(new_content)

print("✅ tariff10.txt обновлён! 10 случайных ключей готовы.")
print("Raw ссылка для клиентов: https://raw.githubusercontent.com/ТВОЙЮЗЕР/ТВОЙРЕПО/main/tariff10.txt")
