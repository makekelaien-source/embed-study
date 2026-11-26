sample-check.exe: main.o sample.o
	gcc main.o sample.o -o sample-check.exe

main.o: main.c sample.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c main.c -o main.o

sample.o: sample.c sample.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c sample.c -o sample.o
