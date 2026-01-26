import sys
import os

# 添加本地库路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))
from bs4 import BeautifulSoup

# 自闭合标签列表（根据作业说明）
SELF_CLOSING_TAGS = {
    'br', 'hr', 'img', 'link', 'base', 'area', 'input', 'source', 'meta'
}


def count_nodes(tag):
    """
    计算一个标签及其所有子标签的数量
    注意：自闭合标签只算1个节点
    """
    if tag.name in SELF_CLOSING_TAGS:
        return 1

    # 对于非自闭合标签，计算所有子孙标签
    all_children = tag.find_all(True)
    return len(all_children) + 1


def parse_arguments():
    """
    解析命令行参数，支持三种功能：
    功能1: mytool.py 文件路径 下界,上界        (只按节点数量)
    功能2: mytool.py 文件路径 标签名           (只按标签名)
    功能3: mytool.py 文件路径 标签名 下界,上界 (组合功能)
    """
    path = sys.argv[1]
    tag_name = None
    min_nodes = 1
    max_nodes = 1000
    function_type = 1  # 1:只节点数量, 2:只标签名, 3:组合

    if len(sys.argv) == 3:
        if ',' in sys.argv[2]:
            # 功能1: 只有节点范围
            bounds = sys.argv[2].split(',')
            if len(bounds) == 2:
                min_nodes = int(bounds[0])
                max_nodes = int(bounds[1])
            function_type = 1
        else:
            # 功能2: 只有标签名
            tag_name = sys.argv[2]
            function_type = 2

    elif len(sys.argv) >= 4:
        # 功能3: 标签名 + 节点范围
        tag_name = sys.argv[2]
        bounds = sys.argv[3].split(',')
        if len(bounds) == 2:
            min_nodes = int(bounds[0])
            max_nodes = int(bounds[1])
        function_type = 3

    return path, tag_name, min_nodes, max_nodes, function_type


def save_subtrees(matching_tags, original_file_path, tag_name, function_type):
    """
    保存提取的子树到文件
    文件名格式: module_原文件名_标签_结点数_序号.html
    """
    saved_files = []

    # 获取原文件名（不带路径和扩展名）
    original_filename = os.path.basename(original_file_path)
    base_name = os.path.splitext(original_filename)[0]  # 去掉 .html

    # 获取原文件所在目录
    output_dir = os.path.dirname(original_file_path)
    if output_dir == "":
        output_dir = "."  # 当前目录

    # 按节点数量分组，然后为每个节点数量的子树编号
    groups = {}
    for tag, node_count in matching_tags:
        if node_count not in groups:
            groups[node_count] = []
        groups[node_count].append(tag)

    # 为每个节点数量的子树分别编号
    for node_count, tags in groups.items():
        for i, tag in enumerate(tags, 1):
            # 确定标签名显示
            if function_type == 1:
                # 功能1：显示实际标签名
                display_tag = tag.name
            else:
                # 功能2和3：显示指定的标签名
                display_tag = tag_name

            # 生成文件名：module_原文件名_标签_节点数_序号.html
            output_filename = f"module_{base_name}_{display_tag}_{node_count}_{i}.html"
            output_path = os.path.join(output_dir, output_filename)

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(str(tag))
                saved_files.append(output_filename)
                print(f"💾 已保存: {output_filename}")
            except Exception as e:
                print(f"❌ 保存失败 {output_filename}: {e}")

    return saved_files


def process_single_file(file_path, tag_name, min_nodes, max_nodes, function_type):
    """处理单个HTML文件"""
    print(f"\n处理文件: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        print("文件读取成功")

        # 使用 html5lib 解析器可以更好地处理不规范的 HTML
        soup = BeautifulSoup(content, 'html.parser')
        print("HTML 解析成功")

        # 根据功能类型进行不同的过滤
        matching_tags = []
        all_tags = soup.find_all(True)

        print(f"查找条件:")
        if function_type == 1:
            print(f"- 节点数: {min_nodes} 到 {max_nodes}")
        elif function_type == 2:
            print(f"- 标签名: <{tag_name}>")
        elif function_type == 3:
            print(f"- 标签名: <{tag_name}>")
            print(f"- 节点数: {min_nodes} 到 {max_nodes}")

        for tag in all_tags:
            node_count = count_nodes(tag)

            # 根据功能类型检查条件
            if function_type == 1:
                # 功能1: 只检查节点数量
                if min_nodes <= node_count <= max_nodes:
                    matching_tags.append((tag, node_count))
                    print(f"✅ 找到: <{tag.name}> - {node_count} 个节点")

            elif function_type == 2:
                # 功能2: 只检查标签名
                if tag.name == tag_name:
                    matching_tags.append((tag, node_count))
                    print(f"✅ 找到: <{tag.name}> - {node_count} 个节点")

            elif function_type == 3:
                # 功能3: 检查标签名和节点数量
                if tag.name == tag_name and min_nodes <= node_count <= max_nodes:
                    matching_tags.append((tag, node_count))
                    print(f"✅ 找到: <{tag.name}> - {node_count} 个节点")

        print(f"总共找到 {len(matching_tags)} 个符合条件的子树")

        # 保存到文件
        if matching_tags:
            saved_files = save_subtrees(matching_tags, file_path, tag_name, function_type)
            print(f"✅ 成功保存 {len(saved_files)} 个文件")
            return saved_files
        else:
            print("❌ 没有找到符合条件的子树")
            return []

    except Exception as e:
        print(f"处理文件出错：{e}")
        return []


def main():
    print("=== HTML 模块提取工具 ===")
    print("程序开始运行")

    if len(sys.argv) < 2:
        print("用法:")
        print("  功能1 - 按节点数量提取: python mytool.py 文件名 下界,上界")
        print("  功能2 - 按标签名提取:   python mytool.py 文件名 标签名")
        print("  功能3 - 组合功能:       python mytool.py 文件名 标签名 下界,上界")
        print("示例:")
        print("  python mytool.py test.html 2,3       # 提取2-3个节点的所有子树")
        print("  python mytool.py test.html p         # 提取所有<p>标签")
        print("  python mytool.py test.html p 2,3     # 提取2-3个节点的<p>标签")
        return

    target_path, tag_name, min_nodes, max_nodes, function_type = parse_arguments()

    print(f"目标路径: {target_path}")

    if function_type == 1:
        print("功能: 按节点数量提取")
        print(f"节点范围: {min_nodes} 到 {max_nodes} 个节点")
    elif function_type == 2:
        print("功能: 按标签名提取")
        print(f"指定标签: <{tag_name}>")
    elif function_type == 3:
        print("功能: 组合提取")
        print(f"指定标签: <{tag_name}>")
        print(f"节点范围: {min_nodes} 到 {max_nodes} 个节点")

    # 路径存在
    if not os.path.exists(target_path):
        print(f"错误：路径'{target_path}'不存在！")
        return
    else:
        print("路径存在")

    # 文件还是文件夹
    if os.path.isfile(target_path):
        print("这是一个文件")
        process_single_file(target_path, tag_name, min_nodes, max_nodes, function_type)

    else:
        print("这是一个文件夹，开始遍历...")
        # 遍历目录中的所有html文件（不以module开头）
        html_files = []
        for filename in os.listdir(target_path):
            if filename.endswith(".html") and not filename.startswith("module"):
                html_files.append(os.path.join(target_path, filename))

        print(f"找到 {len(html_files)} 个HTML文件需要处理")

        total_saved = 0
        for file_path in html_files:
            saved_files = process_single_file(file_path, tag_name, min_nodes, max_nodes, function_type)
            total_saved += len(saved_files)

        print(f"\n🎉 处理完成！总共保存了 {total_saved} 个模块文件")

    print(f"处理完成：{target_path}")


if __name__ == "__main__":
    main()