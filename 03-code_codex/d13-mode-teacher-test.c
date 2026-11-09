#include <stdio.h>
#include <string.h>
#include "d13-mode-command.h"

int main(void)
{
    const char *inputs[] = {"MODE/  AUTO ", "MODE/MANUAL ", "MODE/  ", " MODE/AUTO",
                            "MODE", "MODE/AUTOX", "MODE/AU TO", "MODE/", "MODEX/AUTO",
                            "MODE/auto", "MODE/AUTO\t", "MODE//AUTO"};
    int expected[] = {1, 2, -2, -3, -1, 0, 0, -2, -3, 0, 0, 0};
    for (size_t i = 0; i < sizeof inputs / sizeof inputs[0]; ++i) {
        char text[16];
        strcpy(text, inputs[i]);
        if (classify_mode(text, sizeof text) != expected[i]) return 1;
    }
    char raw[] = {'A', 'B'};
    char valid[] = "MODE/AUTO";
    if (classify_mode(raw, sizeof raw) != MODE_BAD_BUFFER ||
        classify_mode(NULL, 1) != MODE_BAD_BUFFER ||
        classify_mode(valid, 0) != MODE_BAD_BUFFER) return 1;

    puts("15/15 classifier cases passed");
    return 0;
}
