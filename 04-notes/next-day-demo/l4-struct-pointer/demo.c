#include <stdio.h>
enum HeatLevel { HEAT_LOW=0, HEAT_NORMAL=1, HEAT_HIGH=2 };
struct Sample { int id; int value; enum HeatLevel level; };
static void apply(struct Sample *p, int value) {
    p->value=value;
    if(value<20) p->level=HEAT_LOW;
    else if(value>=30) p->level=HEAT_HIGH;
    else p->level=HEAT_NORMAL;
}
int main(void) {
    struct Sample a={1,25,HEAT_NORMAL};
    struct Sample b=a;
    apply(&a,30);
    if(a.level==HEAT_HIGH) printf("a=%d,%d,HIGH\n",a.id,a.value);
    if(b.level==HEAT_NORMAL) printf("b=%d,%d,NORMAL\n",b.id,b.value);
    return 0;
}
