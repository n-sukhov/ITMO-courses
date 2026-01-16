#1 вариант 
from csv import reader
import random
from xml.dom.minidom import parse


#Задание 1
PRICE_LIMIT = 150
table = []

with open('Lab_2/books-en.csv', 'r', encoding='windows-1251') as csvfile:
    table = list(reader(csvfile, delimiter=';'))
    
name_30_count = 0
for i in table:
    if len(i[1]) > 30:
        name_30_count += 1
print(f"Количество записей с названием длинее 30 символов:{name_30_count}\n\n \
    Поиск книги по автору:\n")
       
while True:
    name = input("ФИО: ")
    fb = True
    print()
    for i in table:
        if i[2].lower() == name.lower() and float(i[6].replace(',', '.')) <= PRICE_LIMIT:
            if fb:
                fb = False
            print(f"ISBN: {i[0]}\n" + \
                f"Название: {i[1]}\n" + \
                f"Год публикации: {i[3]}\n" + \
                f"Издательство: {i[4]}\n" + \
                f"Кол-во скачиваний: {i[5]}\n" + \
                f"Цена: {6}\n")
    if fb:
        print(f"Книг даного автора до {PRICE_LIMIT} рублей не найдено.\n")

    if input("Продолжить? (n если нет): ").lower() == 'n':
        break
        
gen_bib = random.choices(table, k=20)

with open('Lab_2/bibliography.txt', 'w', encoding='utf-8') as file:
    for i in range(20):
        file.write(f"{i + 1} {gen_bib[i][2]}. {gen_bib[i][1]} - {gen_bib[i][3]}\n")
    print("\nБиблиографические ссылки записаны в файл bibliography.txt")
    
#Задание 2
file_path = "Lab_2/currency.xml"

dom = parse(file_path)
ids = dom.getElementsByTagName("Valute")
val_dict = {}
for i in ids:
    name = i.getElementsByTagName("Name")[0].firstChild.data
    value = float(i.getElementsByTagName("Value")[0].firstChild.data.replace(',', '.'))
    val_dict.update({name: value})

print(val_dict)

