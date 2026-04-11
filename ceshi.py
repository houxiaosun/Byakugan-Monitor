from HardwareMonitor.Util import OpenComputer
from HardwareMonitor.Hardware import HardwareType, SensorType

def get_cpu_temperature():
    computer = None
    try:
        computer = OpenComputer(cpu=True)
        computer.Update()

        for hardware in computer.Hardware:
            if hardware.HardwareType == HardwareType.Cpu:
                for sensor in hardware.Sensors:
                    if sensor.SensorType == SensorType.Temperature:
                        val = sensor.Value

                        # 确保值是数字类型，并且有效
                        if isinstance(val, (int, float)) and val > 0:
                            return round(val, 1)

                        else:
                            print(f"警告：温度传感器返回了无效值：{val} (类型：{type(val)})")
                            return None
                break
        return None
    except Exception as e:
        print(f"获取CPU温度失败：{e}")
        return None
    finally:
        if computer:
            computer.Close()
print(get_cpu_temperature())