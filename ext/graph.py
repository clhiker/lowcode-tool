import json
import os

class node_graph:

    def __init__(self, name, path = None):
        if path:
            self.path = path
        else:
            self.path = "./"
        self.file_name = name
        self.nodes_dict = {}
        self.attribution_conect = ["wires",]
        self.wires = []

    #常见连接关系：wires[[]], z, tab, broker, nodes[], links[], group
    def build_graph(self, nodes_data):
        
        if not nodes_data:
            return False
        #导入所有结点
        for node in nodes_data:
            try:
                node_id = node['id']
            except TypeError:
                return False
            # print(node_id)
            self.nodes_dict[node_id] = node  #这里的键是node的id，值是node本身
        
        #导入wire单向边
        for node in nodes_data:
            node_id = node['id']
            if "wires" in node:
                wires = node['wires']
                for wire in wires:
                    if not wire:
                        continue
                    elif type(wire) == list:
                        for i in range(len(wire)):
                            self.wires.append((node_id, wire[i]))
                    else:
                        self.wires.append((node_id, wire))
            #处理特殊情况
            if "in" in node and 'out' in node and type(node['out']) == list:
                for item in node['in']:
                    wires = item['wires']
                    for wire in wires:
                        self.wires.append((node_id, wire['id']))
            if "out" in node and type(node['out']) == list:
                for item in node['out']:
                    wires = item['wires']
                    for wire in wires:
                        self.wires.append((wire['id'], node_id))
        
        #导入nodes单向属性
        for node in nodes_data:
            node_id = node['id']
            if 'nodes' in node:
                if 'nodes' not in self.attribution_conect:
                    self.attribution_conect.append("nodes")
                    setattr(self, 'nodes', [])
                for item in node['nodes']:
                    self.nodes.append((node_id, item))
        
        #导入links单向属性
        for node in nodes_data:
            node_id = node['id']
            if 'links' in node:
                if 'links' not in self.attribution_conect:
                    self.attribution_conect.append("links")
                    setattr(self, 'links', [])
                for item in node['links']:
                    self.links.append((node_id, item))
        
        #导入其他属性
        for node in nodes_data:
            node_id = node['id']
            for key in node.keys():
                if key == 'id' or type(node[key]) != str:
                    continue
                elif node[key] in self.nodes_dict.keys():
                    if key not in self.attribution_conect:
                        self.attribution_conect.append(key)
                        setattr(self, key, [])
                    attr = getattr(self, key)
                    attr.append((node_id, node[key]))
        return True


    def print_graph(self):
        for key in self.nodes_dict.keys():
            print(key)
        for attribution in self.attribution_conect:
            print(attribution)
            attr = getattr(self, attribution)
            print(attr)

    def find_subgraphs(self, min_nodes, max_nodes, ignore_attributions = []):
        total_subgraphs = [0 for _ in range(max_nodes - min_nodes + 1)]
        #对每一个节点，寻找其所有连接节点
        node_situation = {}
        for node_id in self.nodes_dict.keys():
            connected = [node_id,]
            numbers = 1

            i = 0
            #找到完整的封闭子图
            while(i < len(connected)):
                current_node = connected[i]
                #对每一个连接属性
                for attribution in self.attribution_conect:
                    attr = getattr(self, attribution)
                    if attribution in ignore_attributions:
                        continue
                    for edge in attr:
                        if edge[0] == current_node and edge[1] not in connected:
                            connected.append(edge[1])
                            numbers += 1
                i += 1
            # print(numbers, connected)
            if numbers >= min_nodes and numbers <= max_nodes:
                total_subgraphs[numbers - min_nodes] += 1
                self.output_subgraph(numbers, connected, total_subgraphs[numbers - min_nodes], ignore_attributions)
            
            #记录节点的连接情况，方便后面处理
            node_situation[node_id] = [numbers, connected]

        #如果子图有多个入口，添加一部分处理
        node_situation = {node_id: node_situation[node_id] for node_id in node_situation.keys() if node_situation[node_id][0] < max_nodes}
        visited = []

        for node_id in node_situation.keys():
            visited.append(node_id)
            current_numbers = node_situation[node_id][0]
            current_connected = node_situation[node_id][1]

            #####################
            #这里算法可能有点问题，但是还没想好怎么解决
            for other_node_id in node_situation.keys():
                if other_node_id in visited:
                    continue
                other_connected = node_situation[other_node_id][1]
                #判断两个子图是否有交集
                try:
                    intersection = set(current_connected) & set(other_connected)
                except TypeError:
                    continue
                #有交集再合并，确保连通性
                if intersection and intersection != set(current_connected) and intersection != set(other_connected):
                    #合并两个子图
                    for new_node in other_connected:
                        if new_node not in current_connected:
                            current_connected.append(new_node)
                            current_numbers += 1

                    if current_numbers >= min_nodes and current_numbers <= max_nodes:
                        total_subgraphs[current_numbers - min_nodes] += 1
                        self.output_subgraph(current_numbers, current_connected, total_subgraphs[current_numbers - min_nodes], ignore_attributions)
                
                if current_numbers >= max_nodes:
                    break

    def output_subgraph(self, numbers, connected, subgraph_index, ignore_attributions):
        # print(f"Subgraph with {numbers} nodes:")
        # for node_id in connected:
        #     print(f"Node ID: {node_id}")
        # print("-----")

        #以JAON格式输出子图
        #命名格式：module_abc_z_5_2.json
        subgraph_nodes = []
        for node_id in connected:
            try:
                subgraph_nodes.append(self.nodes_dict[node_id])
            except (KeyError, TypeError):
                continue
        subgraph_name = f"module_{self.file_name.split('.')[0]}_{'_'.join(ignore_attributions[i] for i in range(len(ignore_attributions)))}_{numbers}_{subgraph_index}.json"
        subgraph_path = os.path.join('module', subgraph_name)
        with open(subgraph_path, 'w', encoding = 'utf-8') as file:
            json.dump(subgraph_nodes, file, ensure_ascii = False, indent = 4)