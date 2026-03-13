# aubo_ros_driver

遨博机器人 ROS 驱动，已在 `kinetic`、`melodic`、`noetic` 环境下通过编译和运行测试。

## 安装所需工具

请根据实际 ROS 版本修改包名。

```bash
# 安装工业机器人控制接口
sudo apt install ros-kinetic-industrial-robot-status-interface

# 安装 MoveIt
sudo apt install ros-kinetic-moveit

# 安装逆运动学求解器
sudo apt install ros-kinetic-trac-ik-kinematics-plugin
```

## 在 Gazebo 中仿真 AUBO 机器人

以下示例以 `aubo_i5` 为例：

```bash
roslaunch aubo_gazebo aubo_bringup.launch robot_model:=aubo_i5
roslaunch aubo_moveit_config moveit_planning_execution.launch sim:=true robot_model:=aubo_i5
roslaunch aubo_moveit_config moveit_rviz.launch
```

## 生成校准版 URDF

可以使用 `aubo_description/scripts/calibrate_urdf_dh.py` 读取机器人 RPC 返回的 DH 校准补偿，并生成新的校准版 URDF 文件。

> 注意：如果需要提升模型与真实机械臂的一致性，建议优先根据当前机械臂的实际参数生成并验证校准版 URDF，再将其用于后续的可视化、规划和实机联调。校准版 URDF 会直接影响机器人运动学模型、TF 和 MoveIt 规划结果。如果使用了错误的机器人型号、错误的 IP、异常的温度参数，或者加载了与当前机械臂不匹配的校准结果，可能导致显示位姿、碰撞模型以及轨迹规划结果与真实机械臂不一致。建议保留原始 URDF，不要直接覆盖，并优先在仿真、可视化或其他低风险流程中完成验证后，再用于实机。

脚本运行前请确认环境中已安装 `numpy`，并且可以正常导入 `pyaubo_sdk`。

示例命令：

```bash
python3 aubo_description/scripts/calibrate_urdf_dh.py \
  --robot-model aubo_i10H \
  --robot-ip 192.168.15.128 \
  --temperature 20
```

也可以直接将 `--urdf-in` 指定为机器人名称，脚本会自动到 `aubo_description/urdf/` 目录中查找对应的 URDF 文件：

```bash
python3 aubo_description/scripts/calibrate_urdf_dh.py \
  --urdf-in aubo_i10H \
  --robot-ip 192.168.15.128 \
  --temperature 20
```

默认输出路径为 `aubo_description/urdf/<robot_model>_calibrated.urdf`。脚本不会覆盖输入 URDF；如果目标文件已存在，则需要显式传入 `--force`。

生成新的校准版 URDF 后，建议重新编译对应工作空间，以确保新文件被正确安装和加载。

## 驱动真实机械臂

如果需要使用校准版 URDF，建议先完成上述生成和验证流程，再连接实机。

以下示例以 `aubo_i5` 为例，请修改为实际机器人 IP：

```bash
roslaunch aubo_robot_driver aubo_bringup.launch robot_model:=aubo_i5 robot_ip:=192.168.127.128 debug:=false aubo_hardware_interface_node_required:=false
roslaunch aubo_moveit_config moveit_planning_execution.launch robot_model:=aubo_i5
roslaunch aubo_moveit_config moveit_rviz.launch
```

## 单点轨迹运动 Demo

请根据实际机器人修改 `robot_ip` 和 `robot_model`：

```bash
roslaunch aubo_robot_driver aubo_bringup.launch robot_model:=aubo_i5 robot_ip:=192.168.127.128 debug:=false aubo_hardware_interface_node_required:=false
roslaunch aubo_planning aubo_planning_demo.launch robot_model:=aubo_i5
```

## 常见错误与异常处理

### ROS1 环境下 DAE/XML 报错修复

如果在 ROS1 环境中加载 URDF 时出现 `.DAE` 模型相关的 XML 解析报错，可以使用仓库根目录下的 `fix_dae_xml_tags.py` 对 DAE 文件进行修复。

原因说明：
仓库中的部分 DAE 文件默认采用了 ROS2 环境可正常读取的 XML 写法，例如使用 `<author/>` 这类自闭合标签。在 ROS2 环境下通常可以正常解析，但在部分 ROS1 环境中，相关 XML 解析器对 DAE 内容更严格，可能因此触发模型加载失败、URDF 解析报错或显示异常。

`fix_dae_xml_tags.py` 会递归扫描 DAE 文件，并将类似 `<author/>`、`<comments/>`、`<keywords/>`、`<revision/>`、`<subject/>`、`<title/>` 的自闭合标签替换为完整标签，以兼容部分 ROS1 环境下的 XML 解析行为。

默认用法（在仓库根目录执行，仅检查不写入）：

```bash
python3 fix_dae_xml_tags.py
```

默认会处理：

```bash
aubo_description/meshes
```

如果需要修复其他目录，也可以手动传入目标路径：

```bash
python3 fix_dae_xml_tags.py aubo_description/meshes
```

如果确认要真正写回修复结果，请显式加上 `--write`：

```bash
python3 fix_dae_xml_tags.py --write
python3 fix_dae_xml_tags.py aubo_description/meshes --write
```

默认模式下，脚本只会输出哪些 `.dae` 文件“将会被修改”；加上 `--write` 后才会原地修改文件，并输出处理统计信息。若检测到 `.dae` 文件为软链接，脚本会自动跳过并打印提示，以避免误修改链接目标。执行前建议先确认工作区状态，或自行备份相关模型文件。

如果你在 ROS1 中遇到 URDF 加载失败、DAE 贴图或模型解析异常，建议先检查并修复 DAE 文件，再重新编译工作空间并重新加载 URDF。

ROS1 使用 `catkin` 工作空间，请在工作空间根目录执行：

```bash
catkin_make
source devel/setup.bash
```

如果你的环境使用 `catkin build`，也可以执行：

```bash
catkin build
source devel/setup.bash
```
