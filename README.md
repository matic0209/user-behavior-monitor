# User Behavior Monitor

一个基于Python的用户行为监控系统，可以实时监控和分析用户的鼠标和键盘操作，检测异常行为。

## 功能特点

- 实时监控鼠标移动、点击和键盘操作
- 使用机器学习模型分析用户行为
- 检测异常行为并发出警告
- 系统托盘支持
- 详细的日志记录
- 可配置的监控参数

## 系统要求

- Windows 7/10/11 或 macOS 10.14+
- Python 3.8 或更高版本
- 管理员权限（用于监控键盘和鼠标事件）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/user-behavior-monitor.git
cd user-behavior-monitor
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 生成图标：
```bash
python create_icon.py
```

## 使用方法

### 开发模式运行

```bash
python behavior_monitor.py
```

### 打包为可执行文件

Windows:
```bash
build.bat
```

macOS:
```bash
chmod +x build.sh
./build.sh
```

打包后的可执行文件将在 `dist` 目录中生成。

## 配置说明

- 监控间隔：默认每5秒进行一次行为分析
- 异常阈值：可在代码中调整异常判定阈值
- 日志级别：可在代码中调整日志记录级别

## 项目结构

```
user-behavior-monitor/
├── behavior_monitor.py    # 主程序
├── feature_engineering.py # 特征提取
├── behavior_classifier.py # 行为分类
├── create_icon.py        # 图标生成
├── build.bat             # Windows打包脚本
├── build.sh             # macOS打包脚本
├── init_repo.sh         # macOS仓库初始化脚本
├── requirements.txt      # 依赖列表
└── README.md            # 项目文档
```

## 开发说明

1. 特征提取：
   - 支持200+种特征
   - 包括鼠标移动、速度、加速度等特征
   - 可扩展的特征提取框架

2. 行为分析：
   - 基于随机森林的分类模型
   - 支持实时行为分析
   - 可配置的异常检测阈值

3. 用户界面：
   - 使用PyQt5构建
   - 支持系统托盘
   - 实时显示监控状态和分析结果

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。 