import json
import os
import argparse
from tqdm import tqdm
import graph

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding = 'utf-8') as file:
            nodes_data = json.load(file)
    except Exception as e:
        print(f"Error:{e}")
        return
    return nodes_data

# nodes_data = load_json("./big_homework_grade2_1/example.json")
# # print(nodes_data)

# test_graph = graph.node_graph("example.json")
# test_graph.build_graph(nodes_data)
# # test_graph.print_graph()
# test_graph.find_subgraphs(5, 6, "z")

def main():
    parser = argparse.ArgumentParser(description = "JSON 子图提取器")
    parser.add_argument("target", help = "json文件或目录")
    parser.add_argument("bound", type = int, nargs = 2, help = "子图数量范围，eg. 2 3")
    parser.add_argument("ignore_attrs", nargs = '*', help = "忽略的属性")
    args = parser.parse_args()

    target_path = args.target
    min_nodes, max_nodes = args.bound
    ignore_attrs = args.ignore_attrs
    if os.path.isfile(target_path):
        files_to_process = [target_path]
    elif os.path.isdir(target_path):
        files_to_process = [os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith('.json')]
    else:
        print("Invalid target path.")
        return
    
    for file_path in tqdm(files_to_process):
        # print(f"Processing file: {file_path}")
        nodes_data = load_json(file_path)
        if os.path.isdir(target_path):
            g = graph.node_graph(os.path.basename(file_path), target_path)
        else:
            g = graph.node_graph(os.path.basename(file_path))
        if not g.build_graph(nodes_data):
            continue
        g.find_subgraphs(min_nodes, max_nodes, ignore_attrs)

if __name__ == "__main__":
    main()
