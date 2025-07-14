/*
Task: 
Напишите программу которая на основе веденной таблицы выводит полином жегалкина.
Формат ввода: вводится n количество переменных и 2^n строк по n+1 нулей
или единиц (таблица истинности)
Пример ввода:
2
0 0 0
1 0 1
0 1 1
1 1 1
Пример вывода:
a+b+ab
*/

#include <iostream>
#include <string>

void transform(bool *f, const int n) {
    int length = 1 << n;
    for (int i = 0; i < n; ++i) {
        int block_size = 1 << i;
        for (int j = block_size; j < length; j += (block_size << 1)) {
            for (int k = 0; k < block_size; ++k)
                *(f + j + k) = *(f + j + k) ^ *(f + j + k - block_size); 
        }
    }

};

std::string generate_zhegalkin(bool **bool_table, const int rows, const int cols) {
    std::string zheg_pol = "";
    bool f[rows];
    for (int i = 0; i < rows; ++i)
        f[i] = bool_table[i][cols-1];
    transform(f, cols -1);
    bool first_term = true;
    for (int i = 0; i < rows; ++i) {
        if (f[i]) {
            if (!first_term) {
                zheg_pol += "+";
            }
            first_term = false;
            bool var_added = false;
            for (int j = 0; j < cols - 1; ++j) {
                if (bool_table[i][j]) {
                    zheg_pol += ('a' + j);
                    var_added = true;
                }
            }

            if (!var_added) {
                zheg_pol += "1";
            }
        }
    }
    return zheg_pol;
}


int main() {
    int n;
    std::cin >> n;
    int rows = 1 << n;
    int cols = n + 1;

    bool** table = new bool*[rows];
    for (int i = 0; i < rows; ++i)
        table[i] = new bool[cols];

    for (int i = 0; i < rows; ++i)
        for (int j = 0; j < cols; ++j)
            std::cin >> table[i][j];

    std::cout << generate_zhegalkin(table, rows, cols);

    for (int i = 0; i < rows; ++i)
        delete[] table[i];
    delete[] table;
    
    return 0;
}