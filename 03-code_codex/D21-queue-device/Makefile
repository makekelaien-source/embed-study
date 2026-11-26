queue-device-check.exe: test-main.o consume-one.o D19-ring-queue.o D20-device-step.o
	gcc test-main.o consume-one.o D19-ring-queue.o D20-device-step.o -o queue-device-check.exe

test-main.o: test-main.c queue-device.h D19-ring-queue.h D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c test-main.c -o test-main.o

consume-one.o: consume-one.c queue-device.h D19-ring-queue.h D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c consume-one.c -o consume-one.o

D19-ring-queue.o: D19-ring-queue.c D19-ring-queue.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c D19-ring-queue.c -o D19-ring-queue.o

D20-device-step.o: D20-device-step.c D20-device-state.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c D20-device-step.c -o D20-device-step.o
