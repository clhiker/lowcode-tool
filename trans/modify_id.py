#!/usr/bin/env python3
"""
脚本功能：读取JSON文件，将其中的id从数字改为"x.json"格式，并保存到新文件中
"""

import argparse
import json


def modify_json_ids(input_file_path, input_type):
    """
    读取JSON文件，将其中的id从数字改为"x.json"格式，并保存到新文件中

    Args:
        input_file_path (str): 输入JSON文件路径
    """
    # 读取原始JSON文件
    with open(input_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 修改每个项目的id字段
    for item in data:
        if 'id' in item:
            # 将数字ID转换为"x.json"格式
            item['id'] = f"{item['id']}.{input_type}"

            # # 将x.json转换为"x.bpmn"格式
            # item['id'] = item['id'].replace('json', 'bpmn')

    # 按照新的id字段排序
    data.sort(key=lambda x: x['id'])

    # 保存修改后的JSON到新文件
    with open(input_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"已成功处理 {len(data)} 个条目，并保存到 {input_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修改json内的各种缺陷")
    parser.add_argument("input_path", help="输入JSON 文件")
    parser.add_argument("input_type", help="文件类型")

    args = parser.parse_args()

    input_path = args.input_path
    input_type = args.input_type

    modify_json_ids(input_path, input_type)