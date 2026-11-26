events-check.exe: test-main.o run-events.o D20-device-step.o
	gcc test-main.o run-events.o D20-device-step.o -o events-check.exe

test-main.o: test-main.c run-events.h D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c test-main.c -o test-main.o

run-events.o: run-events.c run-events.h D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c run-events.c -o run-events.o

D20-device-step.o: D20-device-step.c D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c D20-device-step.c -o D20-device-step.o
