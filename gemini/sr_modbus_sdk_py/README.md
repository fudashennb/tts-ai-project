# sr-modbus-sdk-py

### Overview
- 本工程是一个示例，示范python3如何通过Modbus与斯坦德AGV通信
- 本工程遵循BSD开源协议，用户可以自由修改、使用
- 本工程仅供学习交流，具体还以Modbus协议为准

### 目录结构
```shell
.
├── LICENSE                                  # license文件
├── README.md                                # 自述文件（本文件）
├── src/
│   ├── sr_modbus_model.py                      # 枚举状态和@dataclass数据类
│   └── sr_modbus_sdk.py                     # sr_modbus_sdk的接口类（主要使用这个文件）
└── test/
    ├── examples/
    │   ├── charge.py                        # 展示充电，例子说明：移动到充电站点开始充电，达到指定电量后停止充电
    │   ├── move_with_goods.py               # 展示搬运，例子说明：空车移动到装货站点，扫码举升货架，载着货架移动到卸货点，放下货架
    │   ├── pause_continue_cancel_move.py    # 展示移动控制的暂停移动，继续移动，结束移动，例子说明：移动过程先暂停移动持续10s，然后后继续移动、继续移动持续5s、结束移动
    │   ├── two_stations_move.py             # 展示站点间移动，例子说明：在两个站点间来回移动10次，并在到达每个站点后等待5s
    │   └── wait_release_action.py           # 展示等待放行，例子说明：移动到站点2，在站点2执行等待放行，在AGV屏幕上确认放行，在这个例子中使用等待10秒放行
    └── mb_test_unit.py                      # sr_modbus_sdk接口的单元测试
```

### 环境配置
* 操作系统：windows10\ubuntu20.04.1
* 编程语言：python3.7
* pymodbus： v2.4.0
* 工作路径: windows：C:\workspace   linux：~/workspace/

### 安装requirements.txt依赖
* pip install -r requirements.txt
