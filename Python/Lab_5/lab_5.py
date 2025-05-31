import re
import csv

# Задание 1
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
text_1 = ''.join(open('Lab_5/task1-en.txt','r').readlines())
pattern_1 = r'\b[a-zA-Z]{3,5}\b|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
matches_1 = [i for i in re.findall(pattern_1, text_1) \
    if not ((is_number(i) and '.' in i and len(i) < 5 and not (i[0] == '+' or i[0] == '-')) or \
        (is_number(i) and '.' in i and len(i) < 6 and (i[0] == '+' or i[0] == '-')) or \
        (is_number(i) and '.' not in i and len(i) < 4 and not (i[0] == '+' or i[0] == '-')) or \
        (is_number(i) and '.' not in i and len(i) < 5 and (i[0] == '+' or i[0] == '-')))]

print("Задание 1:\n", matches_1, end='\n\n')


# Задание 2
text_2 = ''.join(open('Lab_5/task2.html','r').readlines())
pattern_2 = r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>'
matches_2 = set(re.findall(pattern_2, text_2))
print("Задание 2:\n", matches_2, end='\n\n')


# Задание 3
data = ''.join(open('Lab_5/task3.txt','r').readlines())

id_pattern = r'\b\d+\b'
surname_pattern = r'\b[A-ZА-ЯЁ][a-zа-яё]+\b'
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
website_pattern = r'\b(?:https?://|www\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

ids = re.findall(id_pattern, data)
surnames = re.findall(surname_pattern, data)
emails = re.findall(email_pattern, data)
dates = re.findall(date_pattern, data)
websites = re.findall(website_pattern, data)

table = zip(ids, surnames, emails, dates, websites)

with open("Lab_5/output.csv", "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["ID", "Фамилия", "Электронная почта", "Дата регистрации", "Сайт"])
    writer.writerows(table)

    print("Задание 3:\nТаблица сохранена в файл output.csv.")