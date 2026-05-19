import sys
import csv
import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget
import psutil
import GPUtil

# 创建定时器
timer = QTimer()

app = QApplication(sys.argv)#创建一个应用程序对象

is_monitoring = False  # 添加全局变量来跟踪监控状态

# 创建一个主窗口
window = QMainWindow()
window.setWindowTitle("Byakugan Monitor v0.5") # 主窗口名
window.resize(800, 600) # 窗口大小

# 重写关闭事件
def closeEvent(event):
    if is_monitoring:  # 如果监控正在进行中
        # 插入分隔行，表示异常结束
        log_data(None, None, None, None, None, is_separator=True)
    event.accept()  # 接受关闭事件

window.closeEvent = closeEvent  # 绑定关闭事件处理函数

# 在主窗口底部添加状态栏
status_bar = window.statusBar()
status_bar.showMessage("就绪")  # 初始状态

# 创建一个标签页控件
tab_widget = QTabWidget(parent=window)
tab_widget.setGeometry(20, 20, 760, 550)

# 创建实时监控标签页
realtime_tab = QMainWindow()
tab_widget.addTab(realtime_tab, "实时监控")
# 创建历史数据标签页
history_tab = QMainWindow()
tab_widget.addTab(history_tab, "历史数据")

# 在历史数据标签页中添加表格
table = QTableWidget(history_tab)
table.setGeometry(10, 10, 740, 500)
table.setColumnCount(6)#修改记得添加！！！！！！！！！！！！！
table.setHorizontalHeaderLabels(["时间", "CPU使用率", "内存使用率","GPU使用率","GPU温度" ,'磁盘使用率'])#修改记得添加！！！！！！！！！！！！！

# 设置表头左对齐
header = table.horizontalHeader()
header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

def load_history_data():
    """加载并显示历史数据"""
    try:
        with open('hardware_log.csv', 'r') as f:# 读取文件
            lines = f.readlines()

        table.setRowCount(len(lines))

        for row, line in enumerate(lines):
            data = line.strip().split(',')
            for col, value in enumerate(data):
                item = QTableWidgetItem(value.strip())
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 设置单元格左对齐
                # 为分隔行设置不同的样式
                if value.strip().startswith('=') or value.strip().startswith('[会话结束]'):
                    item.setBackground(Qt.lightGray)  # 灰色背景
                    item.setTextAlignment(Qt.AlignCenter)  # 居中显示
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row, col, item)

        table.resizeColumnsToContents()# 自动调整列宽以适应内容

    except FileNotFoundError:
        print("还没有历史数据呢！")
# 当标签切换时触发
def on_tab_changed(index):
    if index == 1:  # 第二个标签（历史数据）
        load_history_data()

tab_widget.currentChanged.connect(on_tab_changed)

#创建CPU标签
label = QLabel("CPU使用率（%）: ", parent = realtime_tab)
label.setAlignment(Qt.AlignLeft) # 调用方法，设置文字居中
label.setGeometry(0, 0, 200, 30) # (x, y,宽度，大小)

# GPU使用率标签
gpu_label = QLabel("GPU使用率（%）: ", parent=realtime_tab)
gpu_label.setAlignment(Qt.AlignLeft)
gpu_label.setGeometry(0, 30, 200, 30)

# GPU温度标签
gpu_temp_label = QLabel("GPU温度（℃）: ", parent=realtime_tab)
gpu_temp_label.setAlignment(Qt.AlignLeft)
gpu_temp_label.setGeometry(0, 60, 200, 30)

#硬盘使用率标签
disk_label = QLabel("磁盘使用率（%）: ", parent=realtime_tab)
disk_label.setAlignment(Qt.AlignLeft)
disk_label.setGeometry(0, 120, 200, 30)

# 磁盘读写速度标签
disk_io_label = QLabel("磁盘IO: ", parent=realtime_tab)
disk_io_label.setAlignment(Qt.AlignLeft)
disk_io_label.setGeometry(0, 150, 400, 30)

#内存标签
mem_label = QLabel("内存占用（%）: ", parent = realtime_tab)
mem_label.setAlignment(Qt.AlignLeft)
mem_label.setGeometry(0, 90, 200, 30)


# 创建一个按钮
button = QPushButton("开始监控", parent = window)
button.move(700, 570)


# 定义更新CPU的函数
def update_cpu():
    if not hasattr(update_cpu, '_initialized'):
        psutil.cpu_percent(interval=None)
        update_cpu._initialized = True

    cpu_usage = psutil.cpu_percent(interval=None)  # 获取CPU使用率
    label.setText(f"CPU使用率: {cpu_usage}%")   # 更新显示
    return cpu_usage  # 返回CPU使用率

# 定义GPU函数
def get_gpu_info():
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        load_percent = int(round(gpu.load * 100))
        return {
            'name': gpu.name,
            'load': load_percent,
            'memory_used': gpu.memoryUsed,
            'memory_total': gpu.memoryTotal,
            'temperature': round(gpu.temperature, 1)  # 温度也舍入到1位小数
        }

    else:
        return None

def update_gpu():
    gpu_info = get_gpu_info()
    print(f"gpu_info: {gpu_info}")
    if gpu_info:
        gpu_load = gpu_info['load']  # 使用率
        print(f"gpu_load 类型: {type(gpu_load)}, 值: {gpu_load}")
        gpu_temp = gpu_info['temperature']  # 温度
        gpu_label.setText(f"GPU使用率: {gpu_load}%")
        gpu_temp_label.setText(f"GPU温度: {gpu_temp}℃")
        return gpu_load, gpu_temp# 返回舍入的值
    else:
        gpu_label.setText("GPU: 未检测到")
        return None, None

#硬盘
def get_disk_usage():
    # 监控系统主分区
    disk_usage = psutil.disk_usage('/').percent  # Linux/macOS
    return disk_usage
def get_disk_io():
    # 获取磁盘I/O计数器
    io_counters = psutil.disk_io_counters()
    return {
        'read_bytes': io_counters.read_bytes,  # 读取字节数
        'write_bytes': io_counters.write_bytes,  # 写入字节数
        'read_count': io_counters.read_count,  # 读取次数
        'write_count': io_counters.write_count  # 写入次数
    }


def update_disk():
    disk_usage = psutil.disk_usage('/').percent
    disk_label.setText(f"磁盘使用率: {disk_usage}%")

    # 获取IO信息（可选）
    io = get_disk_io()
    disk_io_label.setText(f"磁盘IO: R:{io['read_bytes'] // 1024}KB W:{io['write_bytes'] // 1024}KB")

    return disk_usage

#内存
def update_memory():
    mem = psutil.virtual_memory()
    mem_usage = mem.percent  # 获取内存使用率
    mem_label.setText(f"内存占用: {mem_usage}%")
    return mem_usage  # 返回内存使用率
#合并更新函数
def update_all():
    cpu_usage = update_cpu()
    mem_usage = update_memory()
    gpu_usage, gpu_temp = update_gpu()
    disk_usage = update_disk()
    log_data(cpu_usage, mem_usage, gpu_usage, gpu_temp, disk_usage)  # 传递所有数据#修改记得添加！！！！！！！！！！！！！#修改记得添加！！！！！！！！！！！！！#修改记得添加！！！！！！！！！！！！！

timer.timeout.connect(update_all)#关联计时器与总函数

def log_data(cpu_usage, mem_usage,gpu_usage=None, gpu_temp=None, disk_usage=None, is_separator=False):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    """
        记录硬件监控数据到CSV文件

        is_separator: 是否为分隔行
    """
    with open('hardware_log.csv', 'a', newline='') as f:#写入历史数据
        writer = csv.writer(f)
        if is_separator:
            # 插入分隔行
            writer.writerow(["=" * 20, "=" * 10, "=" * 10, "=" * 10, "=" * 10, "=" * 10])
            writer.writerow([f"[会话结束] {timestamp}", "-", "-", "-", "-", "-"])
            writer.writerow(["=" * 20, "=" * 10, "=" * 10, "=" * 10, "=" * 10, "=" * 10])
        else:
            # 正常数据行
            gpu_usage_str = gpu_usage if gpu_usage is not None else 'N/A'
            gpu_temp_str = gpu_temp if gpu_temp is not None else 'N/A'
            disk_usage_str = disk_usage if disk_usage is not None else 'N/A'
            writer.writerow([timestamp, cpu_usage, mem_usage, gpu_usage_str, gpu_temp_str, disk_usage_str])#修改记得添加！！！！！！！！！！！！！
    # 如果当前在历史数据标签页，就自动刷新表格
    if tab_widget.currentIndex() == 1:
        load_history_data()

# 定义状态栏
def on_button_clicked():
    global is_monitoring#声明使用全局变量
    if button.text() == "开始监控":
        button.setText("停止监控")
        timer.start(500)
        status_bar.showMessage("监控已开始...")
        update_all()  # 立即更新一次数据
        is_monitoring = True  # 设置监控状态为True
    else:
        button.setText("开始监控")
        timer.stop()
        status_bar.showMessage("监控已停止")
# 监控结束时插入分隔行
        log_data(None, None, None, None, None, is_separator=True)
        is_monitoring = False  # 设置监控状态为False

button.clicked.connect(on_button_clicked)#连接信号和状态栏

# 显示并运行
window.show()
sys.exit(app.exec())
