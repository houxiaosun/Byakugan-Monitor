import sys
import csv
import os
import subprocess
import threading
import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,QTextEdit,QVBoxLayout,QWidget
from PySide6.QtCore import QObject, Signal
import psutil
import GPUtil
from HardwareMonitor.Util import OpenComputer
from HardwareMonitor.Hardware import HardwareType, SensorType
#上层显示
class FPSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口标志：
        # - FramelessWindowHint：去掉标题栏和边框，让它看起来像悬浮文字
        # - WindowStaysOnTopHint：始终保持在所有窗口最前面（包括游戏）
        # - Tool：让它在任务栏不显示图标，避免干扰
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 创建显示 FPS 的标签
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        # 将标签放入布局
        layout = QVBoxLayout()
        layout.addWidget(self.fps_label)
        self.setLayout(layout)

        # 移动到屏幕右上角
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 150, 10)

    def update_fps(self, fps_value):
        self.fps_label.setText(f"FPS: {fps_value:.1f}")

# 创建定时器
timer = QTimer()
analysis_timer = QTimer()  # 新增的分析定时器
app = QApplication(sys.argv)#创建一个应用程序对象
# 添加全局变量来跟踪监控状态
is_monitoring = False
self_test_active = False          # 自检是否正在进行
self_test_timer = QTimer()        # 用于60秒后结束自检
# 创建一个主窗口
window = QMainWindow()
window.setWindowTitle("Byakugan Monitor v0.7") # 主窗口名
window.resize(800, 600) # 窗口大小


class RealtimeFPSMonitor(QObject):
    """负责定时调用 PresentMon 获取 FPS，并更新浮层"""
    fps_updated = Signal(float)  # 定义信号
    def __init__(self, overlay):
        super().__init__()            # 必须先调用父类初始化
        self.overlay = overlay
        self.process_name = "ForzaHorizon5"
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._sample_fps)
        # 连接信号到浮层的更新函数
        self.fps_updated.connect(self.overlay.update_fps)
    def start(self):
        """开始监控：显示浮层，启动定时器"""
        if self.running:
            return
        self.running = True
        self.overlay.show()#显示浮层
        self.timer.start(2000)  # 每2秒采样一次

    def stop(self):
        """停止监控：隐藏浮层，停止定时器"""
        self.running = False
        self.timer.stop()
        self.overlay.hide()

    def _sample_fps(self):
        # 在后台线程中调用 PresentMon，避免界面卡顿
        def worker():
            duration = 1.5  # 采样1.5秒
            temp_csv = "temp_fps_realtime.csv"
            cmd = [
                "PresentMon-2.4.1-x64.exe",
                "--process_name", self.process_name,
                "--output_file", temp_csv,
                "--timed", str(duration),
                "--no_console_stats",
                "--terminate_after_timed",
                "--stop_existing_session"
            ]
            try:
                # 调用外部程序，等待它执行完成（最长等待 duration + 3 秒）
                subprocess.run(cmd, capture_output=True, timeout=duration + 3)
                if not os.path.exists(temp_csv):
                    return
                # 解析 CSV 文件，提取列（帧间隔时间，单位毫秒）
                frame_times = []
                with open(temp_csv, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ms = row.get('MsBetweenPresents')
                        if ms:
                            try:
                                frame_times.append(float(ms))
                            except ValueError:
                                pass
                # 如果成功读取到帧时间数据
                if frame_times:
                    avg_ms = sum(frame_times) / len(frame_times)
                    fps = 1000.0 / avg_ms if avg_ms > 0 else 0
                    if frame_times:
                        avg_ms = sum(frame_times) / len(frame_times)
                        fps = 1000.0 / avg_ms if avg_ms > 0 else 0
                        # 发射信号，主线程会自动调用 overlay.update_fps
                        self.fps_updated.emit(fps)
                        self._log_fps(fps)
                    # 记录到日志
                    self._log_fps(fps)
            except Exception as e:
                print(f"FPS 采样失败: {e}")
            finally:
                if os.path.exists(temp_csv):
                    os.remove(temp_csv)

        threading.Thread(target=worker, daemon=True).start()

    def _log_fps(self, fps):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('fps_log.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, f"{fps:.1f}"])

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

game_mode_button = QPushButton("🎮 游戏模式", parent=window)
game_mode_button.move(500, 570)


# 创建一个标签页控件
tab_widget = QTabWidget(parent=window)
tab_widget.setGeometry(20, 20, 760, 550)

# 创建实时监控标签页
realtime_tab = QMainWindow()
tab_widget.addTab(realtime_tab, "实时监控")
# 创建历史数据标签页
history_tab = QMainWindow()
tab_widget.addTab(history_tab, "历史数据")
#历史诊断标签页
diagnosis_tab = QMainWindow()
tab_widget.addTab(diagnosis_tab, "诊断历史")

# 在历史数据标签页中添加表格
table = QTableWidget(history_tab)
table.setGeometry(10, 10, 740, 500)
table.setColumnCount(7)#修改记得添加！！！！！！！！！！！！！
table.setHorizontalHeaderLabels(["时间", "CPU使用率","CPU温度", "内存使用率","GPU使用率","GPU温度" ,'磁盘使用率'])#修改记得添加！！！！！！！！！！！！！
#历史诊断表格
diagnosis_text = QTextEdit(diagnosis_tab)
diagnosis_text.setGeometry(10, 10, 740, 500)

# 设置表头左对齐
header = table.horizontalHeader()
header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

def load_diagnosis_history():
    """加载诊断历史"""
    try:
        with open('diagnosis_log.txt', 'r', encoding='utf-8') as f:
            diagnosis_text.setPlainText(f.read())
    except FileNotFoundError:
        diagnosis_text.setPlainText("暂无诊断历史")

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
    if index == 1:  # 历史数据标签页
        load_history_data()
    elif index == 2:  # 诊断历史标签页
        load_diagnosis_history()
tab_widget.currentChanged.connect(on_tab_changed)

#创建CPU使用率标签
label = QLabel("CPU使用率（%）: ", parent = realtime_tab)
label.setAlignment(Qt.AlignLeft) # 调用方法，设置文字居左
label.setGeometry(0, 0, 200, 30) # (x, y,宽度，大小)

#创建CPU温度标签
cpu_temp_label = QLabel("CPU温度（℃）: ", parent = realtime_tab)
cpu_temp_label.setAlignment(Qt.AlignLeft)
cpu_temp_label.setGeometry(0, 30, 200, 30) # (x, y,宽度，大小)

# GPU使用率标签
gpu_label = QLabel("GPU使用率（%）: ", parent=realtime_tab)
gpu_label.setAlignment(Qt.AlignLeft)
gpu_label.setGeometry(0, 60, 200, 30)

# GPU温度标签
gpu_temp_label = QLabel("GPU温度（℃）: ", parent=realtime_tab)
gpu_temp_label.setAlignment(Qt.AlignLeft)
gpu_temp_label.setGeometry(0, 90, 200, 30)

#硬盘使用率标签
disk_label = QLabel("磁盘使用率（%）: ", parent=realtime_tab)
disk_label.setAlignment(Qt.AlignLeft)
disk_label.setGeometry(0, 150, 200, 30)

# 磁盘读写速度标签
disk_io_label = QLabel("磁盘IO: ", parent=realtime_tab)
disk_io_label.setAlignment(Qt.AlignLeft)
disk_io_label.setGeometry(0, 180, 400, 30)

#内存标签
mem_label = QLabel("内存占用（%）: ", parent = realtime_tab)
mem_label.setAlignment(Qt.AlignLeft)
mem_label.setGeometry(0, 120, 200, 30)

# 数据缓存（用于存储一段时间内的数据）#修改记得添加！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
data_cache = {
    'timestamps': [],
    'cpu_usage': [],
    'cpu_temp': [],
    'gpu_usage': [],
    'gpu_temp': [],
    'memory_usage': [],
    "disk_usage": [],
}
MAX_CACHE_SIZE = 120  # 缓存2分钟的数据（500ms×120=60秒）

# 创建一个按钮
button = QPushButton("开始监控", parent = window)
button.move(700, 570)

self_test_button = QPushButton("开始一分钟自检", parent = window)
self_test_button.move(600, 570)

# 定义更新CPU的函数
def update_cpu():
    if not hasattr(update_cpu, '_initialized'):
        psutil.cpu_percent(interval=None)
        update_cpu._initialized = True

    cpu_usage = psutil.cpu_percent(interval=None)  # 获取CPU使用率
    label.setText(f"CPU使用率: {cpu_usage}%")   # 更新显示
    return cpu_usage  # 返回CPU使用率
#cpu温度
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
            'temperature': round(gpu.temperature, 1)
        }

    else:
        return None

def update_gpu():
    gpu_info = get_gpu_info()
    if gpu_info:
        gpu_load = gpu_info['load']  # 使用率
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

#硬盘使用率
def update_disk():
    disk_usage = psutil.disk_usage('/').percent
    disk_label.setText(f"磁盘使用率: {disk_usage}%")

    # 获取IO信息
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
    cpu_temp = get_cpu_temperature()
    mem_usage = update_memory()
    gpu_usage, gpu_temp = update_gpu()
    disk_usage = update_disk()
    if cpu_temp is not None:
        cpu_temp_label.setText(f"CPU温度: {cpu_temp}℃")
    else:
        cpu_temp_label.setText("CPU温度: 未监测")
    log_data(cpu_usage, cpu_temp,mem_usage, gpu_usage, gpu_temp, disk_usage)  # 传递所有数据#修改记得添加！！！！！！！！！！！！！#修改记得添加！！！！！！！！！！！！！#修改记得添加！！！！！！！！！！！！！

# 将数据添加到缓存#修改记得添加！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    timestamp = datetime.datetime.now()
    data_cache['timestamps'].append(timestamp)
    data_cache['cpu_usage'].append(cpu_usage)
    data_cache['cpu_temp'].append(cpu_temp if cpu_temp else 0)
    data_cache['gpu_usage'].append(gpu_usage if gpu_usage else 0)
    data_cache['gpu_temp'].append(gpu_temp if gpu_temp else 0)
    data_cache['memory_usage'].append(mem_usage)
    data_cache['disk_usage'].append(disk_usage)

 # 保持缓存大小
    for key in data_cache:
        if len(data_cache[key]) > MAX_CACHE_SIZE:
            data_cache[key].pop(0)

timer.timeout.connect(update_all)#关联计时器与总函数


def perform_analysis():
    """每分钟执行一次的分析函数"""
    if len(data_cache['timestamps']) < 60:  # 至少收集了30秒数据
        return

    print("正在进行后台分析...")

    # 计算平均值
    cpu_avg = sum(data_cache['cpu_usage']) / len(data_cache['cpu_usage'])
    if data_cache['cpu_temp'] and any(t > 0 for t in data_cache['cpu_temp']):
        cpu_temp_avg = sum(t for t in data_cache['cpu_temp'] if t > 0) / len(
            [t for t in data_cache['cpu_temp'] if t > 0])
    else:
        cpu_temp_avg = None
    gpu_avg = sum(data_cache['gpu_usage']) / len(data_cache['gpu_usage'])
    gpu_temp_avg = sum(data_cache['gpu_temp']) / len(data_cache['gpu_temp'])

    analysis = ""
    suggestion = ""

    # 1. 温度分析（优先）
    if cpu_temp_avg and cpu_temp_avg > 85:
        analysis = "🔥 CPU温度过高！"
        suggestion = "请检查散热器、清灰或更换硅脂，长期高温会缩短硬件寿命"
    elif cpu_temp_avg and cpu_temp_avg > 78:
        analysis = "🌡️ CPU温度偏高"
        suggestion = "建议改善机箱风道或检查散热器安装"
    elif gpu_temp_avg > 85:
        analysis = "🔥 GPU温度过高！"
        suggestion = "显卡可能需要清灰或改善机箱通风"
    elif gpu_temp_avg > 76:
        analysis = "🌡️ GPU温度偏高"
        suggestion = "考虑调整风扇曲线或改善机箱风道"

    # 2. 性能瓶颈分析（在温度正常的前提下）
    if not analysis:  # 如果没有温度问题，再分析性能
        if cpu_avg > 80 and gpu_avg < 70:
            analysis = "💻 "
            suggestion = "CPU经常高负载而GPU有余力，考虑升级CPU或优化软件设置"
        elif gpu_avg > 85 and cpu_avg < 70:
            analysis = "🎮 "
            suggestion = "显卡高负载，考虑升级显卡或降低图形设置"
        elif cpu_avg > 80 and gpu_avg > 80:
            analysis = "⚖️ 均衡负载"
            suggestion = "CPU和GPU协同工作，系统配置均衡"
        else:
            analysis = "✅ 系统状态良好"
            suggestion = "硬件负载正常，继续保持"

    # 3. 特殊场景检测
    # 检测是否在游戏（GPU高负载且温度上升）
    if gpu_avg > 90 and gpu_temp_avg > cpu_temp_avg:
        analysis += " | 检测到游戏负载"
        suggestion += " | 游戏时请确保良好通风"

    # 检测是否在渲染/计算（CPU持续高负载）
    if cpu_avg > 90 and all(usage > 80 for usage in data_cache['cpu_usage'][-30:]):
        analysis += " | 检测到计算密集型任务"
        suggestion += " | 进行渲染/计算时建议监控温度"

    # 显示分析结果
    status_bar.showMessage(f"分析: {analysis} | 建议: {suggestion}", 10000)
    # 或者添加到历史诊断记录中
    save_diagnosis_result(analysis, suggestion)

analysis_timer.timeout.connect(perform_analysis)
analysis_timer.start(60000)  # 每分钟触发一次（60000毫秒）

def save_diagnosis_result(analysis, suggestion):
    """将诊断结果保存到文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('diagnosis_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {analysis} | 建议: {suggestion}\n")
# 如果当前就在诊断标签页，实时刷新
    if tab_widget.currentIndex() == 2:
        load_diagnosis_history()

def log_data(cpu_usage, cpu_temp,mem_usage,gpu_usage=None, gpu_temp=None, disk_usage=None, is_separator=False):
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
            writer.writerow([timestamp, cpu_usage ,cpu_temp,mem_usage, gpu_usage_str, gpu_temp_str, disk_usage_str])#修改记得添加！！！！！！！！！！！！！
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
        analysis_timer.start(60000)  # 启动分析定时器
        self_test_button.setEnabled(False)  # 新增：禁用自检按钮
        is_monitoring = True
    else:
        button.setText("开始监控")
        timer.stop()
        status_bar.showMessage("监控已停止")
# 监控结束时插入分隔行
        log_data(None, None, None, None, None, is_separator=True)
        is_monitoring = False  # 设置监控状态为False
        analysis_timer.stop()  # 停止分析定时器
        self_test_button.setEnabled(True)  # 新增：恢复自检按钮
        is_monitoring = False
button.clicked.connect(on_button_clicked)#连接信号和状态栏

# 自检
def start_self_test():
    global is_monitoring, self_test_active

    # 如果常规监控正在运行，先停止它
    if is_monitoring:
        on_button_clicked()   # 模拟点击“停止监控”，会自动插入分隔行

    # 清空数据缓存，确保分析的是自检期间的60秒数据
    for key in data_cache:
        data_cache[key].clear()

    # 设置状态
    self_test_active = True
    self_test_button.setEnabled(False)   # 自检期间禁用按钮
    button.setEnabled(False)             # 也禁用“开始监控”按钮，防止干扰
    status_bar.showMessage("🔍 一分钟自检已启动，正在收集数据...")

    # 启动数据采集（每500ms）
    timer.start(500)
    update_all()  # 立刻采一次

    # 启动60秒后自动结束的定时器
    self_test_timer.setSingleShot(True)  # 只触发一次
    self_test_timer.timeout.connect(finish_self_test)
    self_test_timer.start(60000)         # 60秒 = 60000毫秒


def finish_self_test():
    global self_test_active

    # 停止数据采集
    timer.stop()
    self_test_active = False

    # 恢复按钮状态
    self_test_button.setEnabled(True)
    button.setEnabled(True)

    # 执行分析（此时缓存中已有约120个数据点）
    if len(data_cache['timestamps']) >= 60:
        perform_analysis()
        status_bar.showMessage("✅ 一分钟自检完成，查看上方诊断结果", 10000)
    else:
        status_bar.showMessage("⚠️ 自检数据不足，请稍后重试", 5000)

    # 在CSV中插入分隔行，标记自检结束
    log_data(None, None, None, None, None, is_separator=True)
    if tab_widget.currentIndex() == 2:#更新标签页
        load_diagnosis_history()

self_test_button.clicked.connect(start_self_test)#连接按钮

# 创建 FPS 浮层对象（先隐藏，需要时再显示）
fps_overlay = FPSOverlay()

# 实例化 FPS 监控器
fps_monitor = RealtimeFPSMonitor(fps_overlay)

def toggle_game_mode():
    if game_mode_button.text() == "🎮 游戏模式":
        fps_monitor.start()
        game_mode_button.setText("🛑 关闭浮层")
    else:
        fps_monitor.stop()
        game_mode_button.setText("🎮 游戏模式")

game_mode_button.clicked.connect(toggle_game_mode)

# 显示并运行
window.show()
sys.exit(app.exec())
