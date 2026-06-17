# auto_audit_visitor_review - 访客审核自动化工具

基于 Python + Edge WebDriver 的访客审核自动化工具，支持 7x24h 不间断运行。

---

## 项目结构

```
auto_audit_visitor_review/
├── src/
│   └── auto_audit_visitor_review/    # 主包
│       ├── __init__.py               # 包初始化
│       ├── __main__.py               # 程序入口
│       ├── core.py                   # 审核自动化核心逻辑
│       └── webdriver_manager.py      # EdgeDriver 管理器
├── tests/                            # 测试目录
│   ├── __init__.py
│   ├── conftest.py                   # pytest 共享配置
│   ├── test_core.py                  # 核心模块测试
│   └── test_webdriver_manager.py     # WebDriver 管理器测试
├── res/                              # 资源文件
├── .gitignore
├── Makefile                          # 命令快捷入口
├── pyproject.toml                    # 项目配置
├── requirements.txt                  # 依赖清单
├── run.py                            # 兼容旧入口
└── setup.bat                         # 环境初始化脚本
```

## 快速开始

### 方式 1：使用 Make（推荐）

```bash
# 创建 venv 并安装依赖
make setup

# 运行程序
make run

# 运行测试
make test

# 打包
make build
```

### 方式 2：使用 setup.bat（Windows）

```bash
.\setup.bat
```

### 方式 3：直接使用 Python

```bash
# 激活虚拟环境后
python -m auto_audit_visitor_review
```

## 运行测试

```bash
# 使用 Make
make test

# 或直接使用 pytest
pytest tests/ -v --cov=src/auto_audit_visitor_review --cov-report=term-missing
```

## 自动化流程

1. 打开审核页面
2. 切换到"已审核"标签
3. 切回"待审核"标签（触发数据刷新）
4. 检查是否存在"同意"按钮
5. 如存在则点击"同意"并确认弹窗
6. 关闭标签页，进入下一轮循环

> 任何步骤失败都会自动跳转到步骤 7，进入下一轮循环，保证 7x24h 不间断运行。