import re
import os
import argparse
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修复AI生成的结果，首先将ai生成的描述保存到 ai_result/xx.md 修复后的文件会保存到 ai_result/xx_result_corrected.md 中")
    parser.add_argument("--name", type=str, help="处理的低代码模板名称")
    parser.add_argument("--file_type", type=str, help="种子模板的后缀")
    args = parser.parse_args()
    
    name = args.name
    result_path = f'ai_result/{name}_result.md'
    fixed_path = f'ai_result/{name}_result_corrected.md'
    file_dir = f'seed_{name}'
    file_type = args.file_type

    new_text = ''
    with open(result_path, 'r') as f:
        content = f.read()
        new_text = ''
        pattern = rf'({file_dir}/\w+\.{file_type})((?:\n[^\n]*)*?)\n*(?=\n{file_dir}/|\Z)'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        for filepath, content in tqdm(matches):
            new_text += filepath + '\n'
            item = content.split('\n')
            # 过滤掉空行和只包含空白字符的行
            lines = [line for line in item if line.strip()]
            if len(lines) == 1:
                new_line = lines[0]
                new_line = new_line.replace('功能标签', '')
                new_line = new_line.replace('功能描述', '')
                if '：' in lines[0]:
                    two_lines = new_line.split('：')
                    new_text += '功能标签：' + two_lines[0] + '\n' + '功能描述：' + two_lines[1] + '\n\n\n'
                elif ' ' in lines[0]:
                    two_lines = new_line.split(' ')
                    new_text += '功能标签：' + two_lines[0] + '\n' + '功能描述：' + two_lines[1] + '\n\n\n'
                elif '，' in lines[0]:
                    code = lines[0]
                    new_text += '功能标签：' + code[:code.find('，')] + '\n' \
                                + '功能描述：' + code[code.find('，')+1:] + '\n\n\n'
                elif '功能描述' in lines[0]:
                    two_lines = lines[0].split('功能描述')
                    new_text += '功能标签：' + two_lines[0] + '\n' + '功能描述：' + two_lines[1] + '\n\n\n'

            elif len(lines) == 2:
                for i in range(len(lines)):
                    if i == 0:
                        if '：' in lines[i]:
                            new_line = '功能标签：' + lines[i][lines[i].find('：')+1:]
                        else:
                            new_line = '功能标签：' + lines[i]
                    if i == 1:
                        if '：' in lines[i]:
                            new_line = '功能描述：' + lines[i][lines[i].find('：')+1:]
                        else:
                            new_line = '功能描述：' + lines[i]
                    new_text += new_line + '\n'
                new_text += '\n\n'
            else:
                new_text += content

    with open(fixed_path, 'w') as f:
        f.write(new_text)