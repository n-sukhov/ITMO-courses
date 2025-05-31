#1 вариант
import json
import requests

#Задание 1
API_KEY = '2f44ab8d94825710392977b37c24d3ac'
ABS_ZER0 = -273.15
city_name = input("Выберете город: ")
try:
    response = requests.post(
        f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}', 
        timeout=1)
    result = json.loads(response.text)

    weather = result["main"]["temp"] + ABS_ZER0
    humidity = result["main"]["humidity"]
    pressure =  result["main"]["pressure"]

    print(f"Температура: {weather: .1f} °C",
        f"Влажность: {humidity} %",
        f"Давление: {pressure} мм.рт.ст.", sep='\n', end="\n\n")
except Exception:
    print("Такого города не существует.\n")

#Задание 2
HH_URL = 'https://api.hh.ru/vacancies'

params = {
    'text': 'ROS2',
    'area': 2,
    'per_page': 5
}

hh_response = requests.get(HH_URL, timeout=5, params=params)

if hh_response.status_code == 200:
    vacancies = hh_response.json()
    for vacancy in vacancies.get('items', []):
        print(f"Название: {vacancy.get('name')}")
        print(f"Компания: {vacancy.get('employer', {}).get('name')}")
        print(f"Город: {vacancy.get('area', {}).get('name')}")
        print(f"Дата публикации: {vacancy.get('published_at')}")
        print(f"Ссылка: {vacancy.get('alternate_url')}\n")
else:
    print(f"Ошибка выполнения запроса: {hh_response.status_code}")
