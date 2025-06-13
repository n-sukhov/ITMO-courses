all: $(patsubst %.c, %, $(wildcard *.c))

%: %.c
	gcc $< -o $@

clean:
	rm -f $(patsubst %.c, %, $(wildcard *.c))