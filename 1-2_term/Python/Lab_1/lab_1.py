# 1 вариант

# Drawing french flag
BLUE = "\u001b[44m"
WHITE = "\u001b[47m"
RED = "\u001b[41m"
RESET = "\u001b[0m"

FLAG_PART = 10 * " "

for i in range(10):
    print(BLUE + FLAG_PART + WHITE + FLAG_PART + RED + FLAG_PART + RESET)
    
print()

# Drawing pattern
LINE = 8 * " "

for i in range(12):
    if i < 4 or i > 7:
        print(BLUE + LINE + RESET + LINE + BLUE + LINE + RESET)
    else:
        print(LINE + BLUE + LINE + RESET + LINE)

print("\n\n")
print("Для корректного отображения заданий \
    3-4 терминал необходимо развернуть так, \
    чтобы вмещалось не менее 55 символов.\n")
# Drawing function
print(WHITE)
print()
for i in range(11):
    print(f"{10 * (10 - i)}".rjust(3),' ', end='')
    for j in range(50):
        y = (j / 5) ** 2
        if y - 5 < 100 - i * 10 and y + 5 >= 100 - i * 10:
            print(RED + ' ' + WHITE, end='')
        else:
            print(WHITE + ' ', end='')
    print('\n')
for i in range(11):
    print(f"   {i} ", end='')
print(RESET)

# Drawing diagram
positive = 0
negative = 0
with open("Lab_1/sequence.txt", encoding="utf-8") as file:
    for i in file:
        if float(i) > 0: positive += 1
        elif float(i) < 0: negative += 1
print(WHITE)
total = positive + negative
positive_perc = positive / total * 100
negative_perc = negative / total * 100
STR_LEN = 10
STR = STR_LEN * ' '
STR_LINE = STR_LEN * '-'
for i in range(20, -1, -1):
    print(f"{i * 5}% {STR_LINE}".rjust(STR_LEN + 5), end='')
    if positive_perc > i * 5:
        print(RED + STR + WHITE, end='')
    elif positive_perc > i * 5 - 5:
        print(f"{positive_perc}%".center(STR_LEN), end='')
    else:
        print(STR_LINE, end='')
        
    print(STR_LINE, end='')
    
    if negative_perc > i * 5:
        print(BLUE + STR + WHITE, end='')
    elif negative_perc > i * 5 - 5:
        print(f"{negative_perc}%".center(STR_LEN), end='')
    else:
        print(STR_LINE, end='')
        
    print(STR_LINE)
print('     ' + STR_LEN * 5 * '=')
print(STR + 4 * ' ' + ">0".center(STR_LEN) + \
    STR + "<0".center(STR_LEN) + STR + RESET)
