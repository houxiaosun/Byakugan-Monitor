import sys
import psutil  # 加入psutil库
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton

#导入pyside模块，用于图形化

app = QApplication(sys.argv)#创建一个应用程序对象

# 创建一个主窗口
window = QMainWindow()
window.setWindowTitle("Byakugan Monitor v0.2") # 主窗口名
window.resize(800, 600) # 窗口大小

label = QLabel("CPU使用率: ", parent=window) #属于window父控件，方便统一管理
label.setAlignment(Qt.AlignCenter) # 调用方法，设置文字居中
label.move(50, 50) # (x, y坐标)

# 创建一个按钮
button = QPushButton("开始监控", parent=window)
button.move(50, 100)

# 创建定时器
timer = QTimer()

# 定义更新CPU的函数
def update_cpu():
    cpu_usage = psutil.cpu_percent(interval=1)  # 获取CPU使用率
    label.setText(f"CPU使用率: {cpu_usage}%")   # 更新显示

timer.timeout.connect(update_cpu)#连接计时器与CPU函数

# 定义槽函数
def on_button_clicked():
    """当按钮被点击时，这个函数会被调用"""
    print("按钮被点击!")
    # 判断按钮当前的文字是什么
    if button.text() == "开始监控":
        button.setText("停止监控")
        timer.start(1000)  # 启动定时器，1000毫秒=1秒触发一次
        label.setText("监控已开始...")# 立即更新一次
    else:
        button.setText("开始监控")
        timer.stop()  # 停止定时器
        label.setText("监控已停止")

button.clicked.connect(on_button_clicked)#连接信号和按钮槽函数

# 显示并运行
window.show()
sys.exit(app.exec())
