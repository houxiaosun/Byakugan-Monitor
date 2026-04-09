「白眼」硬件监视器 - 一个高中生开发的开源、免费、无广告的全能硬件监控工具。

像日向一族的瞳术一样，洞察您计算机的一切状态。

"Byakugan" Hardware Monitor - An open-source, free, ad-free all-in-one hardware monitoring tool developed by a high school student.

See all states of your computer, just like the Hyuga clan's legendary eye technique.

# Byakugan Monitor (白眼监视器)

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)

> **像白眼一样，洞察硬件的一切。**

一个由高中生发起的开源项目，旨在构建一个真正**免费、无广告、功能全面**的硬件监控工具，终结付费软件和信息割裂的现状。

## ✨ 项目愿景

- [ ] **完全免费开源** (Free & Open Source)
- [ ] **毫无广告捆绑** (No Ads)  
- [ ] **全面硬件信息** (CPU, GPU, Memory, Disk, Network, Sensors...)
- [ ] **优雅直观的界面** (Beautiful UI)
- [ ] **跨平台支持** (Windows, Linux, macOS)

## 🚀 当前进度

### v0.5 - 2026-04-07（正在准备打包成.exe）
- **新增**: 磁盘使用率监控功能
- **新增**: 会话分隔线功能，清晰区分不同监控时段
- **优化**: 实时监控标签文字左对齐，界面更整洁
- **新增**: GPU 使用率和温度监控功能
- **重构**: 采用标签页界面，分离实时监控与历史数据

### v0.4 - 2026-04-07  
- **新增**: 历史数据表格查看功能
- **优化**: 使用 QTimer 实现无卡顿实时更新

### v0.3 (2026-04-06)
-**更新**：新增内存占用
-**优化**：优化按钮与数据显示位置
-**重构**：统一数据更新逻辑，采用总调度函数管理

### v0.2 (2026-04-06)
-**更新**：导入PYSide6模块，用计时器管理；采用QTimer计时器，不会卡住界面
-**特点**：图形化显示，操做便捷，可打包

### v0.1 (2026-04-06)
-**功能**：循环打印1秒内的时间和CPU使用率
-**特点**：数据带时间戳，具备可追溯性

**项目刚刚启动！目前正在规划与开发中。**

- **下一步计划**：实现内存数据等多数据获取显示。
- **欢迎任何形式的建议与帮助！**

## 🛠 如何开始

目前项目处于早期开发阶段，但欢迎体验已实现的功能：

1.  克隆本仓库: `git clone https://github.com/houxiaosun/Byakugan-Monitor.git`
2.  安装依赖: `pip install -r requirements.txt`
3.  运行程序: `python src/main.py`

*注：功能正在快速迭代中，接口可能发生变化。*

## 🤝 如何贡献

项目刚起步，欢迎任何形式的建议与帮助！包括但不限于：

-   🐛 提交Bug反馈
-   💡 提出新功能建议
-   📖 完善文档
-   🔧 提交代码补丁

具体贡献指南将在后续完善。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**这只是开始，期待你的加入，一起见证「白眼」的成长！**


