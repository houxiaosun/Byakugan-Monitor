import psutil#加入psutil库
import time

print("开始监测CPU使用率，每1秒打印1次")

try:
    while True:#循环
        cpu_usage = psutil.cpu_percent(interval=1)#获取1秒内的CPU使用率平均值

        current_time = time.strftime("%H:%M:%S")#获取当前时间

        print(f"[{current_time}] CPU使用率: {cpu_usage}%")#打印时间和使用率

except KeyboardInterrupt:
    print("\n监测已停止")