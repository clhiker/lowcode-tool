# 低代码工具集介绍

## ext
> 从json/html 中提取需要的子模块

### ext_html.py
#### 输入示例
- 示例 1：按标签名提取（单文件）
提取 `example.html` 中所有 `<div>` 标签对应的子树：
python ext_html.py example.html div

- 示例 2：按节点数量提取（单文件）
提取 `test.html` 中节点数在 2~3 之间的所有子树：
python ext_html.py test.html 2,3

- 示例 3：组合条件提取（单文件）
提取 `demo.html` 中「`<p> 标签 + 节点数 2~4`」的子树：
python ext_html.py demo.html p 2,4

- 示例 4：批量处理目录文件
处理当前目录下所有 HTML 文件，提取 `<span>` 标签：
python ext_html.py . span
处理指定目录提取 `<template>` 标签且节点数 1~3 的子树：
python ext_html.py D:\html_files template 1,3

#### 输出文件说明

生成的模块文件采用规范化命名，结构如下：
module_原文件名_标签名_节点数_序号.html

各部分含义：
- `module_`：固定前缀，用于区分原文件与生成文件；
- `原文件名`：来源 HTML 文件的名称；
- `标签名`：提取的标签名称；
- `节点数`：该子树包含的节点总数；
- `序号`：同一条件下提取的子树编号（从 1 开始）。

命名示例
- `module_test_p_3_1.html`：从 `test.html` 提取的第 1 个节点数为 3 <p> 标签；
- `module_demo_div_1_3.html`：从 `demo.html` 提取的第 3 个节点数为 1 的 <div> 标签（自闭合标签）。

### ext_json.py
JSON 子图提取器

positional arguments:
  target        json文件或目录
  bound         子图数量范围，eg. 2 3
  ignore_attrs  忽略的属性

options:
  -h, --help    show this help message and exit

### ext_nodered_son.py
positional arguments:
  nodered_dir      输入nodered目录
  son_dir          输出包含特征的子nodered目录
  nodered_content  输入nodered总结路径
  son_content      输出包含特征的子nodered总结路径
  rule             要匹配的特征




## trans
各种文件类型转换工具
### json2xlsx.py
将 JSON 文件转换为 XLSX 格式

positional arguments:
  input_path  输入路径（可以是目录或单个 JSON 文件）
  output_dir  输出 XLSX 文件的目录


### modify_id.py
如果描述文件（content.json）中 id是数字，不是文件名，可以使用它修改
positional arguments:
  input_path  输入JSON 文件
  input_type  文件类型

## git_pull
从github中批量拉取文件
### simple_pull.py
下载数据量 1k 以内推荐使用
options:
  -h, --help            show this help message and exit
  --query QUERY, -q QUERY
                        GitHub 搜索关键字, e.g. "template <script> language:vue"
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        保存的下载路径
  --summary SUMMARY     github文件索引
  --per-page PER_PAGE   results per search page (default 100)
  --max-pages MAX_PAGES
                        max search pages to fetch (safety cap)，默认1000
  --sleep SLEEP         sleep seconds between downloads (politeness)， 默认0.3

### massive_pull.py
下载超过1k的github文件

positional arguments:
  token                 你的github token
  query                 查询语句，eg. @formily react extension:tsx

options:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR     保存的下载文件目录，默认为downloaded
  --content CONTENT     保存的下载文件索引，默认为summary.json
  --range RANGE         每个大小区间的最大下载文件数，默认表示使用github默认限制1000 下载总数目 = stop/win * range
  --start_size START_SIZE
                        最小的起始文件大小，默认为0
  --stop_size STOP_SIZE
                        最大的文件大小，在这个尺寸之外的文件不再处理，默认100000（100k）
  --window_size WINDOW_SIZE
                        窗口大小，即每次搜索区间的文件大小间隔，默认1000
  --file_type FILE_TYPE
                        搜索的文件类型
  --download_interval DOWNLOAD_INTERVAL
                        每次下载的时间间隔，默认0.8s
  --page_interval PAGE_INTERVAL
                        每次翻页的时间间隔， 默认3s

## label
使用ollama大模型为github文件生成标签和描述
### ai_label.py
支持断点续传
options:
  -h, --help            show this help message and exit
  --path_name PATH_NAME
                        种子目录 (default: seed_bpmn)
  --result_file RESULT_FILE
                        输出目录，包含描述的md文件 (default: bpmn_result.md)
  --suffix SUFFIX       文件后缀 (default: .bpmn)
  --domain DOMAIN       领域标签，指处理的文件的领域 (default: bpmn)
  --model MODEL         ollama大模型 (default: qwen2.5:14b)
  --port PORT           使用的 Ollama server 端口 (default: 11434)

### repair_md.py
修复AI生成的结果，首先将ai生成的描述保存到 ai_result/xx.md 修复后的文件会保存到 ai_result/xx_result_corrected.md 中

options:
  -h, --help            show this help message and exit
  --name NAME           处理的低代码模板名称
  --file_type FILE_TYPE
                        种子模板的后缀

### gen_xlsx_result.py
根据AI生成的结果，对比github索引，生成和标准.xlsx一致的文件，在content目录下面保存着原始的xlsx文件

options:
  -h, --help            show this help message and exit
  --name NAME           处理的低代码模板名称
  --file_type FILE_TYPE
                        种子模板的后缀
  --fixed_path FIXED_PATH
                        修正的AI结果文件路径，可以为空

### ai_label_miss.py
补充缺失的文件，通过process_md_result 获得有问题的文件，运行此脚本补充结果
options:
  -h, --help            show this help message and exit
  --path_name PATH_NAME
                        种子目录 (default: seed_bpmn)
  --miss_path MISS_PATH
                        缺失文件列表 (default: miss.txt)
  --result_file RESULT_FILE
                        输出目录，包含描述的md文件 (default: fixed.md)
  --suffix SUFFIX       文件后缀 (default: .bpmn)
  --domain DOMAIN       领域标签，指处理的文件的领域 (default: bpmn)
  --model MODEL         ollama大模型 (default: qwen2.5:14b)
  --port PORT           使用的 Ollama server 端口 (default: 11434)

### fill_template_by_ai.py

python label/fill_template_by_ai.py --model qwen2.5:14b --port 11434

### fill_xaml_template_by_ai.py
用于从模板结构 Excel 中查找“标签6. 功能”或“模板描述”为空的行，调用本地 Ollama 生成并回填。脚本会先自动备份 Excel，再在处理完成后校验是否完全补齐。

options:
  -h, --help            show this help message and exit
  --excel EXCEL         待处理 Excel 路径（默认：xaml-模板结构.xlsx）
  --source_dir SOURCE_DIR
                        源文件目录（默认：xaml）
  --syntax_type SYNTAX_TYPE
                        语法种类，用于提示词（默认：xaml）
  --file_type FILE_TYPE
                        文件类型，用于提示词与缺失文件兜底后缀（默认：xaml）
  --model MODEL         Ollama 模型名（默认：qwen2.5:14b）
  --port PORT           Ollama 服务端口（默认：11434）
  --limit LIMIT         最多处理多少行，0 表示处理全部
  --check_only          只检查空值，不执行 AI 生成

示例：
python label/fill_xaml_template_by_ai.py --check_only
python label/fill_xaml_template_by_ai.py --excel xaml-模板结构.xlsx --source_dir xaml --syntax_type xaml --file_type xaml --model qwen2.5:14b --port 11434

### batch_fix_template_lists.py
用于批量修复 `模板清单/` 下的所有模板结构表。脚本会先统计每个文件的待修复行数，再按文件循环调用 `fill_xaml_template_by_ai.py`，直到修复完成或达到重试上限。

参数来源规则：
- `标签1. 语言和框架` 对应 `syntax_type`
- `标签2. 文件后缀` 对应 `file_type`
- `压缩包` 列中的首个有效值作为源目录名，匹配已解压的模板目录；脚本会自动去掉 `.tar.gz`、`.zip` 等压缩包后缀再查找

输出说明：
- 修复后的文件写入 `模板清单-new/`
- 无需修复的文件会直接拷贝到新目录
- 汇总文件为 `模板清单-new/repair_summary.json`
- 汇总中会记录每个文件修复了多少行、修复前后剩余行数、重试轮次和状态

进度条说明：
- 预扫描阶段显示所有清单文件的统计进度
- 修复阶段显示文件级进度
- 单文件修复时显示重试轮次进度
- `fill_xaml_template_by_ai.py` 内部也会显示行级修复进度

示例：
python label/batch_fix_template_lists.py
python label/batch_fix_template_lists.py --max_rounds 20 --max_stall 5
