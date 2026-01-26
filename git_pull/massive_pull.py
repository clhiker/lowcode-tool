import argparse
import requests
import time
import os
import json
import sys
from tqdm import tqdm
from urllib.parse import quote_plus

# 常量定义
CHUNK_SIZE = 32 * 1024

# 辅助函数
def load_summary(summary_path):
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, list):
                    return obj
        except Exception as e:
            print(f"Warning: cannot load existing summary (starting fresh): {e}")
    return []


def save_summary_atomic(summary_path, summary_list):
    tmp = summary_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(summary_list, f, indent=4, ensure_ascii=False)
    os.replace(tmp, summary_path)
    print(f"Summary updated: {summary_path} (now {len(summary_list)} entries)")


def download_stream_with_progress(url, headers, dest_path):
    tmp_path = dest_path + ".part"
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = r.headers.get("Content-Length")
            total_i = int(total) if total else None

            written = 0
            start = time.time()
            content_buffer = b""
            with open(tmp_path, "wb") as f:
                for chunk in r.iter_content(CHUNK_SIZE):
                    if chunk:
                        content_buffer += chunk
                        f.write(chunk)
                        written += len(chunk)
                        elapsed = time.time() - start  # 计算 elapsed
                        speed = written / (elapsed + 1e-6) / 1024
                        if total_i:
                            pct = written / total_i * 100.0
                            sys.stdout.write(
                                f"\rDownloading {os.path.basename(dest_path)}: "
                                f"{written}/{total_i} bytes ({pct:.2f}%) - {speed:.2f} KB/s"
                            )
                        else:
                            sys.stdout.write(
                                f"\rDownloading {os.path.basename(dest_path)}: "
                                f"{written} bytes - {speed:.2f} KB/s"
                            )
                        sys.stdout.flush()

            # 保存文件（移除了angular检查，因为这不是命令行参数要求的功能）
            os.replace(tmp_path, dest_path)
            return written, total_i, dest_path

    except Exception as e:
        print(f"\nDownload error for {url}: {e}")
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    return None, None, None


def search_and_download(start_size, 
                        end_size, 
                        file_counter, 
                        summary_path, 
                        max_files, 
                        base_query, 
                        headers_json, 
                        headers_raw, 
                        download_dir, 
                        file_type, 
                        download_interval, 
                        page_interval):
                        
    size_part = f"size:{start_size}..{end_size}" if end_size else f"size:>{start_size - 1}"
    full_query = f"{base_query} {size_part}"
    url = f"https://api.github.com/search/code?q={quote_plus(full_query)}&per_page=100"

    page = 1
    downloaded_in_range = 0  # 跟踪当前大小区间已下载的文件数量
    while True:
        resp = requests.get(f"{url}&page={page}", headers=headers_json, timeout=30)
        if resp.status_code != 200:
            print(f"Search error {resp.status_code} for size {start_size}-{end_size or '>'}: {resp.text}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            if not item["name"].lower().endswith(file_type):
                continue

            # 检查是否达到每个大小区间的文件限制
            if max_files is not None and downloaded_in_range >= max_files:
                print(f"Reached max files ({max_files}) for size range {start_size}-{end_size or '>'}. Stopping.")
                return file_counter

            contents_url = item["url"]
            new_name = f"{file_counter}.{file_type}"
            file_path = os.path.join(download_dir, new_name)

            size_bytes, _, saved_path = download_stream_with_progress(contents_url, headers_raw, file_path)
            if saved_path is None:
                continue

            # 加载当前 summary，追加新 entry，然后原子保存
            summary = load_summary(summary_path)
            summary.append({
                "id": f'{file_counter}.{file_type}',
                "repo_full_name": item["repository"]["full_name"],
                "original_html_url": item["html_url"]
            })
            save_summary_atomic(summary_path, summary)

            file_counter += 1
            downloaded_in_range += 1
            time.sleep(download_interval)

        rem = resp.headers.get("X-RateLimit-Remaining")
        if rem and int(rem) < 5:
            reset = resp.headers.get("X-RateLimit-Reset")
            reset_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(reset))) if reset else "unknown"
            print(f"Rate limit low ({rem}), reset at {reset_time}. Stopping.")
            return file_counter

        page += 1
        time.sleep(page_interval)
    return file_counter


def run(args):
    # 设置 GitHub API 头
    HEADERS_JSON = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-code-fetcher/1.0"
    }
    HEADERS_RAW = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "github-code-fetcher/1.0"
    }

    # 创建下载目录
    os.makedirs(args.out_dir, exist_ok=True)

    # 主逻辑
    summary = load_summary(args.content)  # 初始加载，如果存在，继续从 len(summary) + 1 开始
    file_counter = len(summary) + 1  # 从现有 entry 后继续编号
    size_ranges = [(start, start + args.window_size - 1) for start in range(args.start_size, args.stop_size, args.window_size)]

    # 检查并添加大文件范围
    large_url = f"https://api.github.com/search/code?q={quote_plus(args.query + f' size:>{args.stop_size - 1}')}&per_page=1"
    large_resp = requests.get(large_url, headers=HEADERS_JSON)
    if large_resp.status_code == 200 and large_resp.json().get("total_count", 0) > 0:
        size_ranges.append((args.stop_size, None))  # 添加大文件范围

    with tqdm(total=len(size_ranges), desc="Ranges", unit="range") as pbar:
        for range_tuple in size_ranges:
            if isinstance(range_tuple, tuple) and len(range_tuple) == 2:
                start, end = range_tuple
            else:
                start = args.stop_size
                end = None
            file_counter = search_and_download(
                start, end, file_counter, args.content, args.range,
                args.query, HEADERS_JSON, HEADERS_RAW, args.out_dir, args.file_type,
                args.download_interval, args.page_interval
            )
            pbar.update(1)

    print(f"Done! Downloaded {file_counter - 1} files. Tracability info saved to {args.content}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载超过1k的github文件")
    parser.add_argument("token", help="你的github token")
    parser.add_argument("query", help="查询语句，eg. @formily react extension:tsx")
    parser.add_argument("--out_dir", default="downloaded", help="保存的下载文件目录，默认为downloaded")
    parser.add_argument("--content", default="summary.json", help="保存的下载文件索引，默认为summary.json")
    parser.add_argument("--range", type=int, default=1000, help="每个大小区间的最大下载文件数，默认表示使用github默认限制1000 下载总数目 = stop/win * range")
    parser.add_argument("--start_size", type=int, default=0, help="最小的起始文件大小，默认为0")
    parser.add_argument("--stop_size", type=int, default=100000,  help="最大的文件大小，在这个尺寸之外的文件不再处理，默认100000（100k）")
    parser.add_argument("--window_size", type=int, default=1000, help="窗口大小，即每次搜索区间的文件大小间隔，默认1000")
    parser.add_argument("--file_type", required=True, help="搜索的文件类型")
    parser.add_argument("--download_interval", type=float, default=0.8, help="每次下载的时间间隔，默认0.8s")
    parser.add_argument("--page_interval", type=float, default=3, help="每次翻页的时间间隔， 默认3s")

    args = parser.parse_args()
    run(args)
