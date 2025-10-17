import os
import sys
from models.model_manager import ModelManager
from rag import RAGManager


def basic_mock_setup():
    """
    基本设置：初始化模型管理器和RAG管理器
    """
    print("\n=== 基本设置 ===")
    
    # 初始化模型管理器
    # 注意：这里使用了简化的设置，实际使用时需要根据您的环境配置正确的模型
    model_manager = ModelManager()
    
    # 为了演示目的，创建一个简单的模拟模型
    class MockModel:
        def __init__(self):
            self.name = "mock_model"
        
        def generate(self, prompt, **kwargs):
            return {"text": "这是来自模拟模型的回答。由于环境限制，无法使用真实模型。"}
    
    # 注册模拟模型
    model = MockModel()
    model_manager.models["mock_model"] = model
    model_manager.current_model = model
    
    # 初始化RAG管理器
    rag_manager = RAGManager(
        model_manager=model_manager,
        vector_store_type="memory",
        vector_store_params={}
    )
    
    print("模型管理器和RAG管理器初始化完成")
    return rag_manager


def basic_llm_setup():
    """
    基本设置：初始化模型管理器和RAG管理器
    """
    print("\n=== 基本设置 ===")
    
    # 初始化模型管理器
    # 注意：这里使用了简化的设置，实际使用时需要根据您的环境配置正确的模型
    model_manager = ModelManager()
    
    # 注册默认模型
    model_manager.register_default_models()
    
    # 获取可用模型列表
    available_models = model_manager.get_available_models()
    print(f"可用模型: {available_models}")
    
    # 初始化RAG管理器
    rag_manager = RAGManager(
        model_manager=model_manager,
        vector_store_type="memory",
        vector_store_params={}
    )
    
    print("模型管理器和RAG管理器初始化完成")
    return rag_manager


def document_loading(rag_manager:RAGManager):
    """
    文档加载示例
    """
    print("\n=== 文档加载示例 ===")
    
    # 1. 加载asset目录中的所有文档
    print("\n1. 加载asset目录中的所有文档:")
    doc_ids = rag_manager.load_directory()
    print(f"成功加载 {len(doc_ids)} 个文档块")
    
    # 2. 加载指定文件（如果有）
    pdf_file = os.path.join(os.path.dirname(__file__), "asset", "example.pdf")
    if os.path.exists(pdf_file):
        print("\n2. 加载指定PDF文件:")
        doc_ids = rag_manager.load_document(pdf_file)
        print(f"成功加载 {len(doc_ids)} 个文档块")
    else:
        print("\n未找到示例PDF文件，跳过加载")
    
    # 3. 加载URL（如果有网络连接）
    # 注意：取消下面的注释来测试URL加载
    # print("\n3. 加载URL:")
    # try:
    #     doc_ids = rag_manager.load_document("https://example.com")
    #     print(f"成功加载 {len(doc_ids)} 个文档块")
    # except Exception as e:
    #     print(f"加载URL失败: {str(e)}")


def knowledge_base_query(rag_manager:RAGManager):
    """
    知识库查询示例
    """
    print("\n=== 知识库查询示例 ===")
    
    # 示例查询
    queries = [
        "什么是RAG？",
        "RAG系统有哪些基本功能？",
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        try:
            # 执行查询
            result = rag_manager.query(query, k=2)
            
            # 打印结果
            print(f"回答: {result.get('answer', result.get('text', '无回答可用'))}")
            if 'sources' in result:
                print(f"参考来源: {', '.join(result['sources'])}")
        except Exception as e:
            print(f"查询过程中出错: {str(e)}")
            print("注意：由于环境限制，可能无法使用完整的RAG功能，但基本框架已经可以工作。")
    
    # 简化的查询示例
    print(f"\n查询: 系统中共有多少文档？")
    try:
        # 直接获取向量存储中的文档数量
        if hasattr(rag_manager.vector_store, 'count'):
            print(f"回答: 系统中共有 {rag_manager.vector_store.count} 个文档。")
        else:
            # 尝试通过list_documents获取
            docs = rag_manager.list_documents()
            print(f"回答: 系统中共有 {len(docs)} 个文档。")
    except Exception as e:
        print(f"获取文档数量出错: {str(e)}")


def document_management(rag_manager):
    """
    文档管理示例
    """
    print("\n=== 文档管理示例 ===")
    
    # 1. 列出所有文档
    print("\n1. 列出所有文档:")
    docs = rag_manager.list_documents()
    print(f"找到 {len(docs)} 个文档")
    
    # 显示前2个文档的基本信息
    for i, doc in enumerate(docs[:2]):
        print(f"\n文档 {i+1}:")
        print(f"ID: {doc['id']}")
        print(f"源: {doc['metadata'].get('source', '未知')}")
        print(f"内容预览: {doc['content'][:100]}...")
    
    # 2. 如果有文档，尝试获取一个文档的详细信息
    if docs:
        doc_id = docs[0]['id']
        print(f"\n2. 获取文档详情 (ID: {doc_id}):")
        doc = rag_manager.get_document(doc_id)
        if doc:
            print(f"ID: {doc['id']}")
            print(f"元数据: {doc['metadata']}")
    
    # 注意：以下操作会修改向量存储，谨慎使用
    # 3. 删除文档示例
    # if docs and len(docs) > 2:
    #     doc_id_to_delete = docs[-1]['id']
    #     print(f"\n3. 删除文档 (ID: {doc_id_to_delete}):")
    #     success = rag_manager.delete_document(doc_id_to_delete)
    #     print(f"删除结果: {'成功' if success else '失败'}")


def custom_configuration():
    """
    自定义配置示例
    """
    print("\n=== 自定义配置示例 ===")
    
    # 不同的向量存储配置
    print("\n1. 使用自定义内存向量存储配置:")
    custom_rag = RAGManager(
        vector_store_type="memory",
        vector_store_params={}
    )
    print("自定义RAG管理器创建成功")
    
    # 注意：在实际使用中，您需要配置适合您环境的嵌入模型
    print("\n注意：在实际部署时，请配置适合您环境的嵌入模型")
    print("例如，可以使用OpenAI的嵌入模型、本地部署的模型或其他开源嵌入模型")


def main():
    """
    主函数
    """
    print("=== RAG系统使用示例 ===")
    
    # 基本设置
    # rag_manager = basic_setup()
    
    rag_manager = basic_llm_setup()
    # 文档加载
    document_loading(rag_manager)
    
    # 知识库查询
    knowledge_base_query(rag_manager)
    
    # 文档管理
    document_management(rag_manager)
    
    # 自定义配置
    custom_configuration()
    
    print("\n=== 示例演示完成 ===")
    print("提示：在实际应用中，请根据您的具体需求修改和扩展这些示例")


if __name__ == "__main__":
    main()