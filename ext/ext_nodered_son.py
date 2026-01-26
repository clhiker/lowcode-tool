import os
import shutil
import re
import json
import argparse
from tqdm import tqdm

def main(nodered_dir, son_dir, nodered_content, son_content, rule):
    # 定义需要搜索的关键词列表
    all_rules = [
        # r'\s*"id"\s*:',
        # r'\s*"type"\s*:',
        # r'\s*"z"\s*:',
        # r'\s*"wires"\s*:',
        # r'\s*"func"\s*:',
        rule
    ]
    
    os.makedirs(son_dir, exist_ok=True)
    
    with open(nodered_content, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)
    
    filtered_files = []
    result_data = []
    
    # 先清空结果目录
    for filename in os.listdir(son_dir):
        file_path = os.path.join(son_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # 遍历下载目录中的所有文件
    count = 1
    for filename in tqdm(os.listdir(nodered_dir)):
        file_path = os.path.join(nodered_dir, filename)
    
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
        # 检查是否包含任意一个指定的关键词
        matches_any_keyword = False
        for keyword_pattern in all_rules:
            if re.search(keyword_pattern, content, re.IGNORECASE):
                matches_any_keyword = True
                break
    
        if matches_any_keyword:
            filtered_files.append(filename)
    
            # 只有匹配的文件才复制到结果目录
            dest_path = os.path.join(son_dir, f'{count}' + filename[filename.rfind('.'):])
            shutil.copy2(file_path, dest_path)
    
            # 在summary_data中查找匹配项
            # 文件名是数字.json格式，我们需要提取数字部分进行匹配
            file_id = filename[filename.rfind('/') + 1:]
            file_type = filename[filename.rfind('.'):]
            for item in summary_data:
                if item['id'] == file_id:
                    new_item = item.copy()
                    new_item['id'] = count
                    result_data.append(new_item)
                    break
            count += 1
    
    # 按照id对结果进行排序
    result_data.sort(key=lambda x: x['id'])
    new_data = []
    for item in result_data:
        new_id = f'{item["id"]}.json'
        item['id'] = new_id
        new_data.append(item)
    
    with open(son_content, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print(f"筛选完成！共找到{len(filtered_files)}个符合条件的文件。")
    print(f"文件已保存到{son_dir}目录。")
    print(f"对应的记录已保存到{son_content}文件。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取包含各种特征的nodered 文件")
    parser.add_argument("nodered_dir", help="输入nodered目录")
    parser.add_argument("son_dir", help="输出包含特征的子nodered目录")
    parser.add_argument("nodered_content", help="输入nodered总结路径")
    parser.add_argument("son_content", help="输出包含特征的子nodered总结路径")
    parser.add_argument("rule", help="要匹配的特征")

    args = parser.parse_args()

    nodered_dir = args.nodered_dir
    son_dir = args.son_dir
    nodered_content = args.nodered_content
    son_content = args.son_content
    rule = args.rule

    main(nodered_dir, son_dir, nodered_content, son_content, rule)