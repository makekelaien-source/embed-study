device-step.o: D20-device-step.c D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c D20-device-step.c -o device-step.o
