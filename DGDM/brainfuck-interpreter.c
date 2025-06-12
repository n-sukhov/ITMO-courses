#include <stdio.h>
#include <string.h> 

#define MEM_SIZE_CELLS 30000

void interpret(char* start, size_t len);

unsigned char memory[MEM_SIZE_CELLS] = {0};

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Usage: %s brainfuck_code_file.b\n", argv[0]);
        return 1;
    }
    const char* extension = strrchr(argv[1], '.');
    if (extension == NULL || (strcmp(extension, ".bf") != 0 && strcmp(extension, ".b") != 0)) {
        printf("Error: Input file must have .bf or .b extension\n");
        return 1;
    }
    FILE* bf_file = fopen(argv[1], "r");
    if (bf_file) {
        fseek(bf_file, 0, SEEK_END);
        unsigned int bf_file_size = ftell(bf_file);
        fseek(bf_file, 0, SEEK_SET);
        char* bf_code_buffer = malloc(bf_file_size);
        fread(bf_code_buffer, bf_file_size, 1, bf_file);
        interpret(bf_code_buffer, bf_file_size);
        fclose(bf_file);
    }
    else {
        printf("Can't open file %s", argv[1]);
        return 1;
    }
    return 0;
}

void interpret(char* start, size_t len) {
    //do smth
    return;
}