#include <stdio.h>
#include <string.h> 
#include <stdlib.h>
#include <stdbool.h>

#define MEM_SIZE_CELLS 30000

void interpret(const unsigned char* start, const size_t len, unsigned char* memory, const size_t mem_size, bool char_mode);
void print_help();

unsigned char memory[MEM_SIZE_CELLS] = {0};

int main(int argc, char** argv) {
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        print_help();
        return 0;
    }
    if (argc != 3) {
        printf("Usage: %s -mode brainfuck_code_file.b\n(use --help for more information)\n", argv[0]);
        return 1;
    }
    const char* extension = strrchr(argv[2], '.');
    if (extension == NULL || (strcmp(extension, ".bf") != 0 && strcmp(extension, ".b") != 0)) {
        printf("Error: Input file must have .bf or .b extension\n");
        return 1;
    }
    bool char_mode = true;
    if (argv[1] == "-d") char_mode = false;
    FILE* bf_file = fopen(argv[2], "rb");
    if (bf_file) {
        fseek(bf_file, 0, SEEK_END);
        unsigned int bf_file_size = ftell(bf_file);
        fseek(bf_file, 0, SEEK_SET);
        unsigned char* bf_code_buffer = malloc(bf_file_size);
        if (!bf_code_buffer) {
            printf("Memory allocation failed.\n");
            fclose(bf_file);
            return 1;
        }
        if (fread(bf_code_buffer, 1, bf_file_size, bf_file) != bf_file_size) {
            printf("Error reading file.\n");
            free(bf_code_buffer);
            fclose(bf_file);
            return 1;
        }
        interpret(bf_code_buffer, bf_file_size, memory, MEM_SIZE_CELLS, char_mode);
        free(bf_code_buffer);
        fclose(bf_file);
    }
    else {
        printf("Can't open file %s.\n", argv[1]);
        return 1;
    }
    return 0;
}

void interpret(const unsigned char* start, const size_t len, unsigned char* memory, const size_t mem_size, bool char_mode) {
    unsigned char* cell_ptr = memory;
    for (const unsigned char* command = start; command != start + len; ++command) {
        switch(*command) {
            case '>':
                ++cell_ptr;
                if (cell_ptr >= memory + mem_size) {
                    printf("(brainfuck memory) Segmentation fault!\n");
                    return;
                }
                break;
            case '<':
                --cell_ptr;
                if (cell_ptr < memory) {
                    printf("(brainfuck memory) Segmentation fault!\n");
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
                if (char_mode) putchar(*cell_ptr);
                else printf("%d", *cell_ptr);
                break;
            case ',':
                if (char_mode) *cell_ptr = getchar();
                else {
                    int num;
                    scanf("%d", &num);
                    *cell_ptr = (unsigned char) num;
                }
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

void print_help() {
    printf("Brainfuck Interpreter usage:\n");
    printf("\t-c\t\tchar I/O mode\n");
    printf("\t-d\t\tdigit I/O mode\n");
}