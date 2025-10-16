# RAG 知识库项目 - 模型访问层

本项目实现了一个可扩展的模型访问层，支持多种AI模型的统一调用和切换，为RAG知识库系统提供基础支持。

## 功能特点

1. **多种模型支持**
   - Ollama本地模型（deepseek-r1:1.5b）
   - OpenAI API
   - DeepSeek API

2. **统一抽象接口**
   - 所有模型实现相同的接口，便于扩展和替换
   - 支持文本生成和多轮对话两种主要功能

3. **模型管理器**
   - 集中管理多个模型实例
   - 支持动态切换当前使用的模型
   - 提供默认模型注册功能

## 项目结构

```
shantong-ai/
├── models/               # 模型实现目录
│   ├── __init__.py       # 包初始化文件
│   ├── base_model.py     # 模型抽象基类
│   ├── ollama_model.py   # Ollama本地模型实现
│   ├── openai_model.py   # OpenAI模型实现
│   ├── deepseek_model.py # DeepSeek模型实现
│   └── model_manager.py  # 模型管理器
├── example_usage.py      # 使用示例
├── requirements.txt      # 依赖包列表
├── .env                  # 环境变量配置
└── .env.example          # 环境变量配置示例
```

## 环境要求

- Python 3.8+
- 依赖包见 `requirements.txt`

## 安装步骤

1. 安装依赖包
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量
   - 复制 `.env.example` 为 `.env`
   - 根据需要配置相应的API密钥和模型参数
   - 默认已配置Ollama本地模型

## 使用方法

### 基本使用

```python
from models.model_manager import ModelManager

# 创建模型管理器并注册默认模型
manager = ModelManager()
manager.register_default_models()

# 生成文本
prompt = "请简单介绍一下人工智能"
response = manager.generate(prompt, temperature=0.7)
print(response)

# 进行对话
messages = [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "什么是机器学习？"}
]
response = manager.chat(messages)
print(response)
```

### 模型切换

```python
# 查看可用模型
available_models = manager.get_available_models()
print(available_models)

# 切换到特定模型
if "ollama" in available_models:
    manager.set_current_model("ollama")
```

### 运行示例

```bash
python example_usage.py
```

## 扩展开发

要添加新的模型支持，只需要：

1. 创建一个新的类，继承自 `BaseModel`
2. 实现 `generate` 和 `chat` 方法
3. 在模型管理器中注册新模型

## 注意事项

1. 使用OpenAI和DeepSeek模型前，需要在 `.env` 文件中配置相应的API密钥
2. 使用Ollama本地模型前，需要确保Ollama服务正在运行，并且已下载 `deepseek-r1:1.5b` 模型
3. 模型参数如 `temperature` 和 `max_tokens` 可以根据需要调整，以获得不同的生成效果

## 故障排除

- 如果Ollama模型连接失败，请检查Ollama服务是否运行，以及模型名称是否正确
- 如果API调用失败，请检查API密钥是否有效，以及网络连接是否正常