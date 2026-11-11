# L4 新知识：结构体首讲

2026-11-11 同日追加学习；按 weeks-01-12-plan.md 的 L4 顺序推进。L3 PC 主线已授，板端未确认继续保留。声明/头文件/分编译已有 D10–D12 证据，不再作为新知识。L4 struct/enum → 作用域/存储期 → 位宽/位操作 → GPIO 输入；本单元仅 struct。

追加单元容量预案50分钟：首讲15、理解检查5、新核心练习20、验证复盘10。不是另开一个300分钟学习日，实际另计；教师备课排除。

struct 将同一实体的多个字段组织为一个对象，各成员可有不同类型。`struct Sample { int sensor_id; int temperature; };` 定义类型，尚未创建 Sample 对象。尾部分号必需。`struct Sample a = {1,25};` 创建对象，按成员声明顺序初始化。以 `a.temperature` 读取或修改成员；修改某成员不自动修改其他成员。同类型结构体可整体赋值，本例纯 int 成员复制值，两个对象独立；尚不推广到含指针成员的深复制。普通局部对象勿未初始化就读取；结构体大小不能普遍假定等于成员大小之和（布局后续授课）。

教师最小示例：

```c
#include <stdio.h>
struct Sample {
    int sensor_id;
    int temperature;
};
int main(void)
{
    struct Sample a = {1, 25};
    struct Sample b = a;
    b.temperature = 30;
    printf("%d %d %d %d\n", a.sensor_id, a.temperature, b.sensor_id, b.temperature);
    return 0;
}
```

教师验证：严格C11含-Werror编译0诊断，运行退出0，输出 `1 25 1 30`。类型定义由编译器处理；进入main创建a，再用a的值初始化b，最后只改b.temperature，打印时a仍25。没有新增状态码。

讲后短预测：若继续执行 `a.sensor_id=7;`，b.sensor_id为何值？待学生回答，不记录掌握。尚未布置学生代码题；布置前创建并核验空白文件。
