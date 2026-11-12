#include <stdio.h>
#include <stdint.h>
#include <limits.h>
int main(void) {
    uint8_t byte = UINT8_MAX;
    uint16_t id = 1000;
    uint32_t flags = UINT32_C(1) << 12;
    byte = (uint8_t)(byte + 1);
    printf("bits=%u,%u,%u values=%u,%u,%lu\n",
           (unsigned int)(sizeof(uint8_t) * CHAR_BIT),
           (unsigned int)(sizeof(uint16_t) * CHAR_BIT),
           (unsigned int)(sizeof(uint32_t) * CHAR_BIT),
           (unsigned int)byte, (unsigned int)id, (unsigned long)flags);
    return 0;
}
