#include <iostream>
#include <vector>

int main() {
    int n,m;
    std::cin >> n >> m;
    std::vector<bool> adj_matrix(m * m, false);

    for (int k = 0; k < n; ++k) {
        int i, j;
        std::cin >> i >> j;
        --i, --j;
        adj_matrix[i * m + j] = true;
    }
    bool reflexivity = true;
    bool transitivity = true;
    bool symmetry = true;
    bool antisymmetry = true;
    bool antireflexivity = true;

    for (int i = 0; i < m; ++i) {
        if (!adj_matrix[i * m + i]) reflexivity = false;
        else antireflexivity = false;
    }

    for (int i = 0; i < m; ++i)
        for (int j = 0; j < m; ++j)
            for (int k = 0; k < m; ++k)
                if (adj_matrix[i * m + j] && adj_matrix[j * m + k] && !adj_matrix[i * m + k]) {
                    transitivity = false;
                    goto transitivity_check;
                }
    transitivity_check:

    for (int i = 0; i < m; ++i)
        for (int j = 0; j < m; ++j) {
            if (adj_matrix[i * m + j] && !adj_matrix[j * m + i])
                symmetry = false;
            if (adj_matrix[i * m + j] && adj_matrix[j * m + i] && (i != j))
                antisymmetry = false;
            if (!(symmetry || antisymmetry)) goto symmetry_check;
        }
           
    symmetry_check:
    
    if (antireflexivity) std::cout << "Антирефлексивное\n";
    else std::cout << (reflexivity ? "Рефлексивное\n" : "Нерефлексивное\n");
    std::cout << (transitivity ? "Транзитивное\n" : "Нетранзитивное\n");
    std::cout << (symmetry ? "Симметричное\n" : "Несимметричное\n");
    if (antisymmetry) std::cout << "Антисимметричное\n";
    
    return 0;
}