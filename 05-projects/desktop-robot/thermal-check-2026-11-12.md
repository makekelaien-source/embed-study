# 温控与恢复检查

实际板端读取：boot_id 12a1522a-0f48-43ad-aed1-3463ec289254，初查uptime37.5秒，说明再次启动。生产voice_controls.py不存在，profile无min_input_dbfs，上轮候选未完成部署。

CPU热区0/1：passive 70°C、90°C，critical110°C。GPU critical110°C；NPU/DDR critical110°C。skin_zone（thermal_zone7）critical50°C，当前约32.9°C。不能据CPU读到81或90°C就断言未达到任何关机阈值；也不能据skin阈值直接断言它触发了本次关机，未取得临界触发日志。

已应用保守大核上限1716000kHz，回读确认；添加/etc/systemd/system/desktop-robot-frequency.service.d/conservative.conf的ExecStartPost，避免以后频率恢复服务再次覆盖成2.002GHz。daemon-reload完成，未重启整机，未改温控阈值或禁用保护。回退需删除该drop-in并恢复原频率服务，稳定性查明前不执行。

最后采样CPU热区0=44.702°C、热区1=43.214°C、skin=32.940°C。语音服务activating、NRestarts=1；journal明确等待CD002-AUDIO USB音箱，found0，尚未ready。恢复音箱连接后再核对，不把activating记作正常就绪。未执行新压力测试。
