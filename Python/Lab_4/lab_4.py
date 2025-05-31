# 1 вариант
def get_cells_and_value(stuffdict):
    cells = [stuffdict[item][0] for item in stuffdict]
    value = [stuffdict[item][1] for item in stuffdict]        
    return cells, value


def get_memtable(stuffdict, C=4):
    cells, value = get_cells_and_value(stuffdict)
    n = len(value)
    
    V = [[0 for c in range(C+1)] for i in range(n+1)]
        
    for i in range(n+1):
        for a in range(C+1):
            if i == 0 or a == 0:
                    V[i][a] = 0

            elif cells[i-1] <= a:
                    V[i][a] = max(value[i-1] + V[i-1][a-cells[i-1]], V[i-1][a])
            
            else:
                V[i][a] = V[i-1][a]       
    return V, cells, value


def get_selected_items_list(stuffdict, C=4):
    V, cells, value = get_memtable(stuffdict)
    n = len(value)
    res = V[n][C]
    surv_p = res
    c = C
    items_list = []

    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == V[i-1][c]:
            continue
        else:
            items_list.append(list(stuffdict.keys())[i-1])
            res -= value[i-1]
            c -= cells[i-1]

    selected_stuff = []

    for i in items_list:
        for key in stuffdict.keys():
            if key == i:
                for i in range(stuffdict.get(i)[0]):
                    selected_stuff.append(key)

    return selected_stuff, surv_p
  
stuff = {
    'r': (3, 25),
    'p': (2, 15),
    'a': (2, 15),
    'm': (2, 20),
    'i': (1, 5),
    'k': (1, 15),
    'x': (3, 20),
    't': (1, 25),
    'f': (1, 15),
    'd': (1, 10),
    's': (2, 20),
    'c': (2, 20)
}

START_SURV_POINTS = 15 - sum(i[1] for i in stuff.values())

cells_1_4, surv_1 = get_selected_items_list(stuff)
for i in set(cells_1_4):
    del stuff[i]
cells_5_8, surv_2 = get_selected_items_list(stuff)

str_1 = '[' + "], [".join(cells_1_4) + ']'
str_2 = '[' + "], [".join(cells_5_8) + ']'

surv_points = START_SURV_POINTS + 2 * (surv_1 + surv_2)

if surv_points > 0:
    print(str_1)
    print(str_2)
    print(f"\nИтоговые очки выживания: {surv_points}")
else:
    print(f"\nВыжить с таким набором не получится, очки выживания: {surv_points}")
    
