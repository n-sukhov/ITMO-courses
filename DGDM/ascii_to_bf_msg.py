ascii_codes = list(map(int, input().split()))

brainfuck_code = []
current_value = 0

for code in ascii_codes:
    brainfuck_code.append('+' * code)
    brainfuck_code.append('.>\n')

bf_program = ''.join(brainfuck_code)

print("Сгенерированный Brainfuck код:")
print(bf_program)