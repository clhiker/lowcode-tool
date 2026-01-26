#!/usr/bin/env python3
"""
脚本功能：遍历指定目录，将所有的 JSON 文件转换为 XLSX 格式，保持目录结构不变
或者处理单个 JSON 文件
"""

import json
import pandas as pd
from pathlib import Path
import sys
import os
import argparse


def json_to_xlsx_recursive(source_root, target_root, single_file=None):
    # 创建目标根目录（如果不存在）
    target_root = Path(target_root)
    target_root.mkdir(exist_ok=True)

    if single_file:
        # 处理单个文件
        json_file = Path(single_file)
        if not json_file.exists():
            print(f"错误: 文件不存在 - {json_file}")
            return
        if json_file.suffix.lower() != '.json':
            print(f"警告: 文件可能不是 JSON 格式 - {json_file}")

        json_files = [json_file]
        source_root = json_file.parent  # 设置源目录为文件所在目录
    else:
        # 处理目录中的所有 JSON 文件
        source_root = Path(source_root)
        json_files = list(source_root.rglob("*.json"))

    print(f"找到 {len(json_files)} 个 JSON 文件")

    for json_file in json_files:
        try:
            if single_file:
                print(f"正在处理单个文件: {json_file}")
                # 单个文件直接使用文件名作为输出名
                xlsx_file = target_root / json_file.with_suffix('.xlsx').name
            else:
                print(f"正在处理: {json_file.relative_to(source_root)}")

                # 计算相对于源根目录的路径
                relative_path = json_file.relative_to(source_root)

                # 构建目标 XLSX 文件路径，将扩展名从 .json 改为 .xlsx
                xlsx_file = target_root / relative_path.with_suffix('.xlsx')

            # 读取 JSON 文件
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 将数据转换为 DataFrame
            # 如果数据是字典列表，则直接转换
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # 如果是单个字典，则将其转换为包含一行的 DataFrame
                df = pd.DataFrame([data])
            else:
                if single_file:
                    print(f"  跳过 {json_file}: 不支持的数据类型")
                else:
                    print(f"  跳过 {json_file.relative_to(source_root)}: 不支持的数据类型")
                continue

            # 确保目标目录存在
            xlsx_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存为 XLSX 文件
            df.to_excel(xlsx_file, index=False, engine='openpyxl')

            if single_file:
                print(f"  已保存: {xlsx_file} ({len(df)} 行 x {len(df.columns)} 列)")
            else:
                print(f"  已保存: {xlsx_file.relative_to(target_root)} ({len(df)} 行 x {len(df.columns)} 列)")

        except Exception as e:
            if single_file:
                print(f"  处理 {json_file} 时出错: {str(e)}")
            else:
                print(f"  处理 {json_file.relative_to(source_root)} 时出错: {str(e)}")

    if single_file:
        print(f"\n转换完成！XLSX 文件保存在 {target_root}")
    else:
        print(f"\n转换完成！XLSX 文件保存在 {target_root}，目录结构已保持不变")


def main():
    parser = argparse.ArgumentParser(description="将 JSON 文件转换为 XLSX 格式")
    parser.add_argument("input_path", help="输入路径（可以是目录或单个 JSON 文件）")
    parser.add_argument("output_dir", help="输出 XLSX 文件的目录")

    args = parser.parse_args()

    input_path = args.input_path
    output_dir = args.output_dir

    # 检查输入路径是否存在
    if not Path(input_path).exists():
        print(f"错误: 输入路径不存在 - {input_path}")
        sys.exit(1)

    if os.path.isfile(input_path):
        # 当作单个文件处理
        json_to_xlsx_recursive(None, output_dir, single_file=input_path)
    else:
        # 当作目录处理
        json_to_xlsx_recursive(input_path, output_dir)


if __name__ == "__main__":
    main()