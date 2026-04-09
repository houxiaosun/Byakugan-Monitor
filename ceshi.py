import psutil
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Byakugan Monitor v0.2")
window.resize(800, 600)

label = QLabel("CPU使用率: 0%", parent=window)
label.setAlignment(Qt.AlignCenter)
label.setGeometry(50, 50, 200, 30)

button = QPushButton("开始监控", parent=window)
button.setGeometry(50, 100, 100, 30)

# 创建定时器
timer = QTimer()

def update_cpu():
    """更新CPU使用率显示"""
    cpu_usage = psutil.cpu_percent(interval=0)  # 立即返回，不阻塞
    label.setText(f"CPU使用率: {cpu_usage}%")

def on_button_clicked():
    """开始/停止监控"""
    if timer.isActive():
        timer.stop()
        button.setText("开始监控")
    else:
        timer.start(1000)  # 每1000毫秒（1秒）触发一次
        button.setText("停止监控")
        update_cpu()  # 立即更新一次

# 连接定时器超时信号到更新函数
timer.timeout.connect(update_cpu)
button.clicked.connect(on_button_clicked)

window.show()
sys.exit(app.exec())
