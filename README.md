# RAG 知识库系统

一个可扩展的检索增强生成（RAG）知识库系统，支持多种文档格式加载、向量存储和知识库问答功能。

## 项目架构

项目采用模块化设计，具有良好的扩展性和可维护性。主要包括以下几个核心模块：

1. **文档加载器（document_loaders）**：负责从不同来源加载文档并进行预处理
2. **向量存储（vector_stores）**：管理向量的存储、检索和更新
3. **RAG管理器（rag）**：集成文档加载和向量存储，提供完整的RAG功能
4. **模型管理（models）**：管理AI模型的调用

## 项目结构

```
shantong_ai/
├── document_loaders/     # 文档加载器模块
│   ├── __init__.py      # 加载器工厂和自动注册
│   ├── base.py          # 加载器基类定义
│   ├── pdf_loader.py    # PDF文件加载器
│   ├── word_loader.py   # Word文件加载器
│   ├── excel_loader.py  # Excel文件加载器
│   ├── text_loader.py   # 文本文件加载器
│   ├── url_loader.py    # URL加载器
│   └── feishu_loader.py # 飞书文档加载器
├── vector_stores/       # 向量存储模块
│   ├── __init__.py      # 存储工厂和自动注册
│   ├── base.py          # 存储基类定义
│   └── faiss_store.py   # FAISS向量存储实现
├── rag/                 # RAG核心模块
│   └── __init__.py      # RAG管理器实现
├── models/              # 模型管理模块
│   ├── __init__.py
│   ├── base_model.py
│   ├── ollama_model.py
│   ├── openai_model.py
│   ├── deepseek_model.py
│   └── model_manager.py
├── asset/               # 文档资源目录
├── example_usage.py     # 模型使用示例
├── example_rag_usage.py # RAG使用示例
├── requirements.txt     # 项目依赖
├── .env                 # 环境变量配置
└── .env.example         # 环境变量配置示例
```

## 核心功能

### 1. 多格式文档支持

- **PDF文档**：支持读取PDF文件并提取文本内容
- **Word文档**：支持读取.docx格式的Word文档
- **Excel文档**：支持读取.xlsx和.xls格式的Excel文档
- **文本文件**：支持读取.txt、.md、.csv等多种文本格式
- **URL链接**：支持从网页获取内容
- **飞书文档**：支持从飞书获取文档内容

### 2. 向量存储管理

- **FAISS存储**：使用FAISS进行高效的向量搜索
- **持久化**：支持向量存储的保存和加载
- **CRUD操作**：支持文档的增删改查操作
- **源管理**：支持按文件名或URL进行文档管理

### 3. 模型管理

- **多种模型支持**：Ollama本地模型、OpenAI API、DeepSeek API
- **统一抽象接口**：所有模型实现相同的接口，便于扩展和替换
- **模型管理器**：集中管理多个模型实例，支持动态切换

### 4. RAG功能

- **文档加载**：支持加载单个文件或目录下的所有文件
- **知识库查询**：基于检索到的相关文档生成回答
- **源引用**：在回答中包含引用来源
- **自定义配置**：支持配置向量存储和模型参数

## 安装和配置

### 1. 创建Python环境

```bash
# 使用conda创建虚拟环境
conda create -n rag_env python=3.9
conda activate rag_env

# 或者使用virtualenv
python -m venv rag_env
source rag_env/bin/activate  # Linux/Mac
rag_env\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
# 安装基本依赖
pip install faiss-cpu numpy pandas openpyxl python-docx requests beautifulsoup4 tiktoken PyPDF2

# 如果使用GPU版本的FAISS
# pip install faiss-gpu
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，根据需要配置以下环境变量：

```
# OpenAI API配置
OPENAI_API_KEY=your_api_key

# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key

# 飞书文档API配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

## 使用方法

### 模型管理使用

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

### RAG系统使用

```python
from rag import RAGManager
from models.model_manager import ModelManager

# 初始化模型管理器
model_manager = ModelManager()
model_manager.register_default_models()

# 初始化RAG管理器
rag_manager = RAGManager(
    model_manager=model_manager,
    vector_store_type="faiss",
    vector_store_params={
        "persist_directory": "./vector_store",
        "index_name": "my_index"
    }
)

# 加载文档
rag_manager.load_directory("./asset")

# 查询知识库
result = rag_manager.query("什么是RAG？")
print("回答:", result["answer"])
print("参考来源:", result["sources"])
```

### 运行示例

```bash
# 运行模型管理示例
python example_usage.py

# 运行RAG系统示例
python example_rag_usage.py
```

## 扩展开发

### 添加新的文档加载器

1. 在`document_loaders`目录下创建新的加载器文件，例如`my_loader.py`
2. 实现`BaseDocumentLoader`接口：

```python
from document_loaders.base import BaseDocumentLoader, Document

class MyFileLoader(BaseDocumentLoader):
    def load(self, path, **kwargs):
        # 实现文档加载逻辑
        # 返回Document对象列表
        pass
    
    @staticmethod
    def get_loader_info():
        return {
            "name": "my_loader",
            "extensions": [".myext"]
        }
```

加载器会自动注册到工厂中，无需额外配置。

### 添加新的向量存储

1. 在`vector_stores`目录下创建新的存储文件，例如`my_store.py`
2. 实现`BaseVectorStore`接口：

```python
from vector_stores.base import BaseVectorStore
from document_loaders.base import Document

class MyVectorStore(BaseVectorStore):
    # 实现所有必要的方法
    def add_documents(self, documents):
        # 实现添加文档的逻辑
        pass
    
    def search(self, query, k=5, **kwargs):
        # 实现搜索逻辑
        pass
    
    # 实现其他必要方法...
```

向量存储会自动注册到工厂中，无需额外配置。

### 添加新的模型

要添加新的模型支持，只需要：

1. 创建一个新的类，继承自 `BaseModel`
2. 实现 `generate` 和 `chat` 方法
3. 在模型管理器中注册新模型

## 注意事项

1. **文件编码**：确保所有文本文件使用UTF-8编码，以避免中文乱码问题
2. **API密钥**：使用OpenAI、DeepSeek和飞书模型前，需要在`.env`文件中配置相应的API密钥
3. **Ollama模型**：使用Ollama本地模型前，需要确保Ollama服务正在运行，并且已下载相应模型
4. **内存使用**：处理大量文档时，请注意内存使用情况
5. **性能优化**：对于大规模知识库，可以考虑使用GPU加速的FAISS或其他更高效的向量存储
6. **模型参数**：参数如 `temperature` 和 `max_tokens` 可以根据需要调整，以获得不同的生成效果

## 故障排除

- 如果Ollama模型连接失败，请检查Ollama服务是否运行，以及模型名称是否正确
- 如果API调用失败，请检查API密钥是否有效，以及网络连接是否正常
- 如果文档加载失败，请检查文件格式是否受支持，文件是否存在且可访问