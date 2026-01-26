import os
import argparse
from tqdm import tqdm
from ollama import chat
from ollama import ChatResponse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Label Tool for processing files")
    parser.add_argument("--path_name", type=str, default="seed_bpmn", help="种子目录 (default: seed_bpmn)")
    parser.add_argument("--result_file", type=str, default="bpmn_result.md", help="输出目录，包含描述的md文件 (default: bpmn_result.md)")
    parser.add_argument("--suffix", type=str, default=".bpmn", help="文件后缀 (default: .bpmn)")
    parser.add_argument("--domain", type=str, default="bpmn", help="领域标签，指处理的文件的领域 (default: bpmn)")
    parser.add_argument("--model", type=str, default="qwen2.5:14b", help="ollama大模型 (default: qwen2.5:14b)")
    parser.add_argument("--port", type=str, default="11434", help="使用的 Ollama server 端口 (default: 11434)")
    
    args = parser.parse_args()
    
    # 设置 Ollama 服务器地址
    os.environ['OLLAMA_HOST'] = f"127.0.0.1:{args.port}"
    
    path_name = args.path_name
    result_file = args.result_file
    suffix = args.suffix
    DOMIN = args.domain
    MODEL = args.model

    def get_processed_files(result_file):
        """从结果文件中提取已处理的文件列表"""
        processed_files = set()
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取所有包含的行作为已处理的文件
                lines = content.split("\n")
                for line in lines:
                    if line.strip().endswith(suffix):
                        # 如果是相对路径或绝对路径，都加入集合
                        processed_files.add(line.strip())
        return processed_files


    def get_all_files(path_name):
        """获取所有文件"""
        all_files = []
        for name in os.listdir(path_name):
            if name.endswith(suffix):
                all_files.append(os.path.join(path_name, name))
        return all_files



    # 获取已处理的文件列表
    processed_files = get_processed_files(result_file)
    print(f"已处理 {len(processed_files)} 个文件")

    # 获取所有文件
    all_files = get_all_files(path_name)
    print(f"总共找到 {len(all_files)} 个文件")

    # 找出未处理的文件
    unprocessed_files = [f for f in all_files if f not in processed_files]
    print(f"剩余 {len(unprocessed_files)} 个文件待处理")

    # 处理未完成的文件
    for file_name in tqdm(unprocessed_files, desc="Processing files"):
        with open(file_name, 'r', encoding='utf-8') as f:
            text = f.read()[:1000]
            
            response: ChatResponse = chat(model=MODEL, messages=[
                {"role": "system", "content": f"你是一个前端开发专家，对于{DOMIN}的语法有很深的了解。你的回答不要包含 ** 符号"},
                {
                    "role": "user",
                    "content": (
                        f"请读取下面的{DOMIN}文件，并为其生成一个功能标签（不超过8个汉字），"
                        "功能描述（不少于60个字符，不超过100个字符,不应该包含任何子标签，不要分段，不要包含 ** 符号）。"
                        "文件内容如下：\n" + text + "\n请中文回答我的问题"
                    )
                },
            ])

        with open(result_file, 'a+', encoding='utf-8') as f:
            f.write(file_name + '\n')
            f.write(response.message.content)
            f.write('\n\n\n')

