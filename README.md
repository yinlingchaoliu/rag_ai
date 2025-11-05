# X公司知识库RAG系统

## 项目简介

X公司知识库RAG系统是一个基于检索增强生成技术的智能问答系统，能够从企业知识库中检索相关信息并生成准确的回答。本系统现已升级为WebUI版本，支持多主题聊天、文件上传分类存储、历史记录持久化等功能。

## 主要功能

### 核心RAG功能
1. **文档管理**：支持多种格式文档的导入、解析和分块
2. **向量存储**：使用FAISS实现高效的向量检索
3. **智能问答**：基于检索到的文档生成准确回答
4. **统一的配置管理系统**：支持YAML配置和环境变量覆盖，使用Pydantic进行数据验证

### WebUI功能特性
1. **多主题聊天**
   - 支持创建多个独立的聊天主题
   - 每个主题有独立的名称和文件存储目录
   - 主题名称可自定义修改

2. **文件管理**
   - 支持上传PDF、Word、Excel、TXT、Markdown等格式文档
   - 文件自动分类存储到`upload`文件夹的子目录
   - 支持文件记录的删除（不会删除实际文件）

3. **聊天功能**
   - 基于RAG技术的智能问答
   - 聊天记录本地SQLite持久化存储
   - 支持单条消息的删除
   - 历史记录与文件关联

4. **知识库管理**
   - 支持知识库内容搜索
   - 可查看所有上传的文件

## 系统架构

本项目采用MVC架构设计，主要组件包括：

- **Model**: `sqlite/sqlite_manager.py` - 负责数据持久化，管理聊天主题、消息和文件记录
- **View**: `webui.py` - 基于Gradio的Web界面，提供用户交互
- **Controller**: `server.py` - 业务逻辑层，集成RAG能力和数据库操作
- **入口**: `main.py` - 程序主入口，启动WebUI服务

## 项目结构

```
rag_ai/
├── main.py                 # 程序主入口
├── server.py               # RAG服务层
├── webui.py                # WebUI界面实现
├── requirements.txt        # 依赖列表
├── upload/                 # 文件上传目录
│   ├── [topic_id1]/        # 主题1的文件目录
│   └── [topic_id2]/        # 主题2的文件目录
├── db/
│   └── sqlite/
│       └── rag_chat.db     # SQLite数据库文件
├── sqlite/
│   └── sqlite_manager.py   # 数据库管理器
└── README.md               # 项目说明文档
```

## 安装配置

### 环境要求

- Python 3.8+
- pip

### 依赖安装

```bash
pip install -r requirements.txt
```

### 配置说明

项目采用分层配置策略，使用ConfigManager统一管理配置，配置项分为以下几类：

1. **LLM加载参数**：模型类型、模型名称、基础URL等
2. **Embedding模型参数**：模型类型、模型名称、维度等
3. **FAISS数据库参数**：向量存储目录、索引文件名等
4. **RAG系统参数**：搜索参数、阈值设置等
5. **文档处理参数**：分块大小、重叠大小等
6. **日志参数**：日志级别、日志文件路径等

配置文件位于 `config/default_config.yml`，敏感信息通过环境变量在 `.env` 文件中配置。

## 配置管理系统

### ConfigManager类

ConfigManager负责从YAML文件和环境变量加载配置，并提供类型安全的访问方式：

- 支持从`config/default_config.yml`加载默认配置
- 支持通过环境变量覆盖配置
- 支持使用`${ENV_VAR}`格式在YAML中引用环境变量
- 使用Pydantic实体类进行数据验证和类型提示
- 保持向后兼容性，原有配置变量依然可用

### 配置实体类

使用Pydantic定义了以下配置实体类：

- `LLMConfig`：管理LLM加载参数
- `EmbeddingConfig`：管理嵌入模型参数
- `FAISSConfig`：管理FAISS数据库参数
- `RAGConfig`：管理RAG系统参数
- `DocumentConfig`：管理文档处理参数
- `LoggingConfig`：管理日志参数
- `AppConfig`：包含所有配置的完整实体类

## 使用方法

### 初始化配置

系统启动时会自动加载配置：

```python
from config.config_manager import config_manager

# 获取分类配置（返回Pydantic实体类）
llm_config = config_manager.get_llm_config()
embedding_config = config_manager.get_embedding_config()
faiss_config = config_manager.get_faiss_config()

# 使用配置（类型安全）
model_type = llm_config.model_type
model_name = llm_config.model_name

# 或者使用点号语法获取配置项
chunk_size = config_manager.get("document.chunk_size")
```

### 更新配置

```python
# 更新配置
config_manager.update_config({
    "llm": {
        "temperature": 0.3
    }
})

# 获取更新后的配置
updated_temperature = config_manager.get_llm_config().temperature
```

## 主要模块

### config/ 配置管理模块

- `__init__.py`: 配置管理模块初始化
- `config_manager.py`: ConfigManager类实现
- `config_entities.py`: Pydantic配置实体类定义
- `default_config.yml`: 默认配置文件

## 代码变更说明

### 新增文件

- `config/__init__.py`: 配置管理模块初始化
- `config/config_manager.py`: ConfigManager类实现
- `config/config_entities.py`: Pydantic配置实体类定义
- `config/default_config.yml`: 默认配置文件
- `test/test_config_manager.py`: 配置管理器测试

### 修改文件

- `config.py`: 使用ConfigManager替换原有配置方式，保持向后兼容

## 项目结构

```
rag_ai/
├── x_rag_app.py          # 主应用入口脚本（新增）
├── config.py             # 系统配置文件（新增）
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
│   ├── __init__.py      # RAG管理器实现
│   └── rag_system.py    # RAG系统核心实现（新增）
├── models/              # 模型管理模块
│   ├── __init__.py
│   ├── base_model.py
│   ├── ollama_model.py
│   ├── openai_model.py
│   ├── deepseek_model.py
│   └── model_manager.py
├── embedding/           # 嵌入模型模块
│   ├── __init__.py
│   ├── base.py
│   └── ollama_embedding.py
├── db/                  # 数据存储目录（新增）
│   └── vector_store/     # FAISS向量存储文件
├── example_usage.py     # 模型使用示例
├── example_rag_usage.py # RAG使用示例
├── requirements.txt     # 项目依赖
├── .env                 # 环境变量配置
├── .env.example         # 环境变量配置示例
└── README.md            # 项目说明文档
```

## 核心功能

### 1. 多格式文档支持

- **PDF文档**：支持读取PDF文件并提取文本内容
- **Word文档**：支持读取.docx格式的Word文档
- **Excel文档**：支持读取.xlsx和.xls格式的Excel文档
- **文本文件**：支持读取.txt、.md、.csv等多种文本格式
- **URL链接**：支持从网页获取内容
- **飞书文档**：支持从飞书获取文档内容

### 2. 高效向量检索

- **FAISS存储**：使用FAISS进行高性能相似性搜索
- **持久化存储**：向量数据库自动持久化到本地文件，支持增量更新
- **源过滤**：支持按源文件路径过滤文档
- **相似度阈值**：可配置的相似度过滤阈值

### 3. 智能问答

- **Ollama本地模型**：支持本地部署的大语言模型
- **DeepSeek API**（可选）：支持云端大语言模型服务
- **上下文构建**：智能构建问答上下文，提高回答质量
- **源引用**：支持在回答中包含引用来源信息

### 4. 文档管理

- **批量加载**：支持批量导入多个文件或整个目录
- **递归处理**：支持递归处理子目录中的文档
- **源管理**：支持查看、删除特定源的文档
- **清空功能**：支持清空整个知识库

## 安装和配置

### 1. 创建独立Python环境

```bash
# 创建并激活conda环境
conda create -n rag_system python=3.12
conda activate rag_system

# 或使用virtualenv
virtualenv rag_system
source rag_system/bin/activate  # Mac/Linux
rag_system\Scripts\activate    # Windows
```

### 自动激活指定 conda环境 
```shell
# 自动激活 .conda-env 文件中指定的conda环境
FILE=./.conda-env
if [[ -f "$FILE" ]]; then
    CONDA_ENV=$(<$FILE)
    conda activate $CONDA_ENV
fi
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装和配置Ollama（推荐）

1. 从 [Ollama官方网站](https://ollama.ai/) 下载并安装Ollama
2. 拉取所需的模型：
   ```bash
   ollama pull llama3.1:8b-instant
   ```
3. 确保Ollama服务正在运行（默认地址：http://localhost:11434）

### 4. 配置系统

系统通过`config.py`文件进行配置，主要配置项包括：

- **向量存储配置**：FAISS存储路径和文件名
- **嵌入模型配置**：模型类型、名称、维度和API地址
- **LLM配置**：模型类型、名称、温度和最大token数
- **RAG系统配置**：搜索参数、相似度阈值等

所有配置项都可以通过环境变量覆盖，格式为配置项的大写形式。例如：

```bash
export LLM_MODEL_NAME="llama3.1:70b"
export RAG_SEARCH_TOP_K="10"
python x_rag_app.py
```

## 使用方法

### 1. 加载文档

```bash
# 加载单个文档
python x_rag_app.py load /path/to/your/document.pdf

# 加载多个文档
python x_rag_app.py load /path/to/doc1.pdf /path/to/doc2.docx

# 加载目录中的所有文档
python x_rag_app.py load /path/to/documents/

# 递归加载目录及其子目录中的文档
python x_rag_app.py load /path/to/documents/ --recursive
```

### 2. 查询知识库

```bash
# 单次查询
python x_rag_app.py query "公司的核心业务是什么？"

# 查询并显示源文档信息
python x_rag_app.py query "公司的核心业务是什么？" --show-sources

# 自定义返回的相关文档数量
python x_rag_app.py query "公司的核心业务是什么？" --top-k 3

# 交互式查询模式
python x_rag_app.py
```

### 3. 管理文档源

```bash
# 列出所有文档源
python x_rag_app.py list-sources

# 删除指定文档源
python x_rag_app.py delete-source /path/to/document.pdf

# 清空知识库
python x_rag_app.py clear
```
# pip install faiss-gpu
```

## 注意事项

1. **Ollama服务**：确保Ollama服务正在运行，默认地址为http://localhost:11434
2. **依赖安装**：如果缺少特定文档格式的加载器，程序会提示缺少相应的依赖包
3. **向量存储**：首次运行会自动创建向量存储目录，后续运行会加载已有数据
4. **性能优化**：对于大量文档，可以考虑调整`DEFAULT_CHUNK_SIZE`和`DEFAULT_CHUNK_OVERLAP`参数
5. **环境变量**：敏感信息（如API密钥）建议通过环境变量设置，不要硬编码在配置文件中

## 故障排除

### 常见问题

1. **Ollama连接失败**：检查Ollama服务是否运行，地址是否正确
2. **文档加载失败**：确保安装了相应格式的处理依赖
3. **内存不足**：对于大型知识库，考虑增加系统内存或分批处理文档
4. **回答质量不佳**：调整`RAG_SEARCH_TOP_K`参数或切换到更大的模型

### 日志

系统日志默认输出到控制台，可通过修改`LOG_FILE`配置项将日志保存到文件。

## 扩展建议

1. **添加更多文档加载器**：支持更多格式如HTML、CSV等
2. **实现查询扩展**：提高低质量查询的检索效果
3. **添加缓存机制**：缓存热门查询的结果，提高响应速度
4. **添加文档摘要**：为长文档生成摘要，便于快速浏览
5. **实现Web界面**：提供图形化操作界面，提升用户体验

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

### 添加新的向量存储

1. 在`vector_stores`目录下创建新的存储文件，例如`my_store.py`
2. 实现`BaseVectorStore`接口并注册到工厂：

```python
from vector_stores.base import BaseVectorStore, vector_store_factory

@vector_store_factory.register("my_store")
class MyVectorStore(BaseVectorStore):
    # 实现所有必要方法
    pass
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
2. 实现`BaseVectorStore`接口并使用装饰器注册到工厂：

```python
from vector_stores.base import BaseVectorStore, vector_store_factory
from document_loaders.base import Document

@vector_store_factory.register("my_store")
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

使用装饰器注册后，可通过工厂直接创建：`vector_store_factory.create("my_store", **params)`

### 添加新的嵌入模型

1. 在`embedding`目录下创建新的模型文件，例如`my_embedding.py`
2. 实现`BaseEmbeddingModel`接口并注册到工厂：

```python
from embedding.base import BaseEmbeddingModel, embedding_model_factory

@embedding_model_factory.register("my_embedding")
class MyEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, **kwargs):
        # 初始化模型配置
        pass
    
    def embed(self, texts):
        # 实现批量文本嵌入
        return embeddings
    
    def embed_query(self, query):
        # 实现查询文本嵌入
        return embedding
    
    @property
    def get_name(self):
        # 返回模型名称
        return "my_embedding"
```

使用方法：`embedding_model = embedding_model_factory.create("my_embedding", **params)`

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
7. **嵌入模型**：使用Ollama嵌入模型时，请确保Ollama服务正常运行且已拉取nomic-embed-text:latest模型
8. **向后兼容**：新的embedding模块和改进的向量存储功能与原有系统完全兼容，可无缝集成到现有项目中

## 故障排除

- 如果Ollama模型连接失败，请检查Ollama服务是否运行，以及模型名称是否正确
- 如果API调用失败，请检查API密钥是否有效，以及网络连接是否正常
- 如果文档加载失败，请检查文件格式是否受支持，文件是否存在且可访问

## WebUI运行指南

### 1. 安装Gradio依赖

```bash
pip install gradio>=4.0.0
```

### 2. 运行WebUI

```bash
python main.py
```

WebUI将在http://0.0.0.0:7860启动。

## 使用说明

1. **创建新主题**
   - 在输入框中输入问题，点击"创建新主题"
   - 主题名称默认为问题的前15个字符

2. **上传文件**
   - 展开"上传文件"面板
   - 选择或拖拽文件到上传区域
   - 点击"添加到知识库"按钮

3. **聊天交互**
   - 在输入框中输入问题，按回车或点击"发送"
   - 系统会基于已上传的文档内容生成回答

4. **管理主题**
   - 可以从下拉菜单切换不同主题
   - 使用"重命名主题"按钮修改主题名称
   - 使用"删除主题"按钮删除整个主题（不会删除实际文件）

5. **查看知识库**
   - 点击"📚 查看知识库"按钮打开知识库面板
   - 可以搜索知识库内容或查看所有上传文件

## 注意事项

1. 删除聊天主题不会删除对应的上传文件
2. 删除文件记录不会删除实际文件
3. 建议定期清理不需要的文件，避免占用过多存储空间
4. 对于大型文档，可能需要较长时间处理

## 版本历史

- v2.0.0: WebUI版本，支持多主题聊天、文件上传分类存储、历史记录持久化等功能
- v1.0.0: 初始版本，核心RAG功能实现