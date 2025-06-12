#include <stdio.h>
#include <string.h> 

#define MEM_SIZE_CELLS 30000

void interpret(char* start, size_t len, unsigned char* memory, size_t mem_size);

unsigned char memory[MEM_SIZE_CELLS] = {0};

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Usage: %s brainfuck_code_file.b", argv[0]);
        return 1;
    }
    const char* extension = strrchr(argv[1], '.');
    if (extension == NULL || (strcmp(extension, ".bf") != 0 && strcmp(extension, ".b") != 0)) {
        printf("Error: Input file must have .bf or .b extension");
        return 1;
    }
    FILE* bf_file = fopen(argv[1], "rb");
    if (bf_file) {
        fseek(bf_file, 0, SEEK_END);
        unsigned int bf_file_size = ftell(bf_file);
        fseek(bf_file, 0, SEEK_SET);
        char* bf_code_buffer = malloc(bf_file_size);
        if (!bf_code_buffer) {
            printf("Memory allocation failed.");
            fclose(bf_file);
            return 1;
        }
        if (fread(bf_code_buffer, 1, bf_file_size, bf_file) != bf_file_size) {
            printf("Error reading file.");
            free(bf_code_buffer);
            fclose(bf_file);
            return 1;
        }
        interpret(bf_code_buffer, bf_file_size, memory, MEM_SIZE_CELLS);
        free(bf_code_buffer);
        fclose(bf_file);
    }
    else {
        printf("Can't open file %s.", argv[1]);
        return 1;
    }
    return 0;
}

void interpret(char* start, size_t len, unsigned char* memory, size_t mem_size) {
    char* cell_ptr = memory;
    for (char* command = start; command != start + len; ++command) {
        switch(*command) {
            case '>':
                ++cell_ptr;
                if (cell_ptr >= memory + mem_size) {
                    printf("(brainfuck memory) Segmentation fault!");
                    return;
                }
                break;
            case '<':
                --cell_ptr;
                if (cell_ptr < memory) {
                    printf("(brainfuck memory) Segmentation fault!");
                    return;
                }
                break;
            case '+':
                ++(*cell_ptr);
                break;
            case '-': 
                --(*cell_ptr);
                break;
            case '.':
                putchar(*cell_ptr);
                break;
            case ',':
                *cell_ptr = getchar();
                break;
            case '[':
                if (*cell_ptr == 0) {
                    int bracket_depth = 1;
                    while (bracket_depth) {
                        ++command;
                        if (*command == '[') ++bracket_depth;
                        else if (*command == ']') --bracket_depth;
                    }
                }
                break;
            case ']':
                if (*cell_ptr != 0) {
                    int bracket_depth = 1;
                    while (bracket_depth) {
                        --command;
                        if (*command == '[') --bracket_depth;
                        else if (*command == ']') ++bracket_depth;
                    }
                }
                break;
        }
    }
}