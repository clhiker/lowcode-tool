#!/usr/bin/env python3
# main.py
"""
GitHub 搜索并批量下载代码文件脚本（1000以内）

功能：
 - 使用 GitHub Code Search API (/search/code) 按查询拉取结果并分页
 - 对每个搜索到的文件使用 contents API 下载原始文件（Accept: v3.raw），显示下载进度
 - 将每个下载文件按序号重命名为 1, 2, 3 ...（保留扩展名，如果无法推断则无扩展）
   local_path_before_rename（预期原路径信息）、local_path_after_rename（实际保存路径）、sha、size_bytes、timestamp、downloaded

重要（你要求）：
 - Token 已写进代码（变量 GITHUB_TOKEN）。请替换为你自己的 PAT（personal access token）。
 - 如果你希望我改为从环境变量读取 token，请告诉我。

限制与注意：
 - GitHub Search API 对单次查询的返回结果在实践中常被限制（约 1000 条），若需要抓取更多请拆分查询（按 created/pushed 时间段或 repo 列表等）。
 - 请对 `query` 使用合适的 qualifiers（language:, repo:, path:, filename: 等）以缩小范围。
 - 频繁大规模请求会触发 rate limit，请合理使用 --sleep 参数。

用法示例：
  python3 main.py --query 'template <script> language:vue' --output-dir ./downloaded 

"""

import os
import sys
import time
import json
import argparse
import requests
import mimetypes
from urllib.parse import quote_plus

API_BASE = "https://api.github.com"

CHUNK_SIZE = 32 * 1024  # 32KB


def safe_mkdir(path):
    os.makedirs(path, exist_ok=True)


def load_summary(summary_path):
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, list):
                    return obj
        except Exception as e:
            print("Warning: cannot load existing summary (will start fresh):", e)
    return []


def save_summary_atomic(summary_path, summary_list):
    tmp = summary_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(summary_list, f, indent=2, ensure_ascii=False)
    os.replace(tmp, summary_path)


def guess_extension_from_content_type(ct):
    if not ct:
        return ""
    ct = ct.split(";")[0].strip()
    ext = mimetypes.guess_extension(ct)
    if not ext:
        if ct == "text/plain":
            return ".txt"
        if ct.startswith("text/"):
            return ".txt"
        if ct == "application/javascript":
            return ".js"
    return ext or ""


def download_stream_with_progress(url, headers, dest_path):
    """
    下载流并显示进度。将内容写入 dest_path（原子性先写 .part 再改名）。
    返回 (bytes_written, content_length_or_None, response_headers, final_path)
    """
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = r.headers.get("Content-Length")
        try:
            total_i = int(total) if total else None
        except:
            total_i = None

        tmp_path = dest_path + ".part"
        safe_mkdir(os.path.dirname(tmp_path) or ".")
        written = 0
        start = time.time()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                written += len(chunk)
                # progress line
                if total_i:
                    pct = written / total_i * 100.0
                    elapsed = time.time() - start
                    speed = written / (elapsed + 1e-6)
                    sys.stdout.write(f"\rDownloading: {os.path.basename(dest_path)} {written}/{total_i} bytes ({pct:.2f}%) - {speed/1024:.2f} KB/s")
                else:
                    elapsed = time.time() - start
                    speed = written / (elapsed + 1e-6)
                    sys.stdout.write(f"\rDownloading: {os.path.basename(dest_path)} {written} bytes - {speed/1024:.2f} KB/s")
                sys.stdout.flush()
        sys.stdout.write("\n")
        os.replace(tmp_path, dest_path)
        return written, total_i, r.headers.copy(), dest_path


def fetch_search_page(q, page, per_page, headers):
    url = f"{API_BASE}/search/code?q={quote_plus(q)}&per_page={per_page}&page={page}"
    r = requests.get(url, headers=headers, timeout=30)
    # if r.status_code != 200: caller will handle exceptions
    r.raise_for_status()
    return r.json(), r.headers


def get_headers(token, raw=False):
    h = {"Accept": "application/vnd.github.v3.raw" if raw else "application/vnd.github.v3+json",
         "User-Agent": "github-code-fetcher/1.0"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def process_search_and_download(query, output_dir, summary_path,
                                token, per_page=100, max_pages=1000, sleep_between=0.3):
    safe_mkdir(output_dir)
    summary = load_summary(summary_path)
    counter = len(summary)  # next id = counter + 1

    headers_search = get_headers(token, raw=False)
    headers_raw = get_headers(token, raw=True)

    page = 1
    while page <= max_pages:
        print(f"\nFetching search page {page} ...")
        try:
            data, resp_headers = fetch_search_page(query, page, per_page, headers_search)
        except requests.HTTPError as e:
            print("HTTP error during search:", e)
            # try to show body if possible
            try:
                print("Response body:", e.response.text[:1000])
            except Exception:
                pass
            break
        except Exception as e:
            print("Error during search:", e)
            break

        if page == 1:
            total_count = data.get("total_count", 0)
            print(f"Search reported total_count = {total_count} (note: search may be capped).")

        items = data.get("items", [])
        if not items:
            print("No items on this page, stopping.")
            break

        for it in items:
            counter += 1
            repo = it.get("repository") or {}
            repo_full = repo.get("full_name") or "unknown/unknown"
            repo_html = repo.get("html_url") or ""
            path_in_repo = it.get("path") or ""
            html_url = it.get("html_url") or ""
            api_url = it.get("url") or ""  # contents API endpoint for the file

            print(f"\n[#{counter}] {repo_full}:{path_in_repo}")
            # Determine extension from original path if present
            _, ext = os.path.splitext(path_in_repo)
            ext = ext or ""

            # Decide numeric filename
            numeric_basename = str(counter)
            target_name = numeric_basename + ext
            final_local_path = os.path.join(output_dir, target_name)

            # local_path_before_rename (info, not actually saved there)
            owner_repo = repo_full.replace("/", "__")
            local_before = os.path.join(output_dir, owner_repo, path_in_repo)

            download_ok = False
            size_bytes = None
            sha = None
            download_url_from_info = None

            # Perform download via contents API url with Accept raw
            try:
                # Attempt raw download streaming
                bytes_written, total_i, resp_headers, saved_path = download_stream_with_progress(api_url, headers_raw, final_local_path)
                size_bytes = bytes_written

                # If extension missing, try guess from content-type
                if not ext:
                    ct = resp_headers.get("Content-Type")
                    guessed = guess_extension_from_content_type(ct)
                    if guessed:
                        new_name = numeric_basename + guessed
                        new_path = os.path.join(output_dir, new_name)
                        os.replace(final_local_path, new_path)
                        final_local_path = new_path
                        ext = guessed

                # fetch JSON metadata to get sha and download_url if possible
                try:
                    info_headers = get_headers(token, raw=False)
                    info_resp = requests.get(api_url, headers=info_headers, timeout=20)
                    if info_resp.ok:
                        info_json = info_resp.json()
                        sha = info_json.get("sha")
                        download_url_from_info = info_json.get("download_url")
                except Exception:
                    pass

                download_ok = True
            except requests.HTTPError as e:
                print(f"HTTP error while downloading {html_url}: {e}")
                try:
                    print("Response body:", e.response.text[:1000])
                except Exception:
                    pass
                download_ok = False
            except Exception as e:
                print(f"Error while downloading {html_url}: {e}")
                download_ok = False

            entry = {
                "id": counter,
                "repo_full_name": repo_full,
                "repo_html_url": repo_html,
                "original_path_in_repo": path_in_repo,
                "original_html_url": html_url,
                "api_url": api_url,
                "local_path_before_rename": local_before,
                "local_path_after_rename": os.path.abspath(final_local_path) if download_ok else None,
                "downloaded": bool(download_ok),
                "size_bytes": size_bytes,
                "sha": sha,
                "download_url_from_api": download_url_from_info,
                "timestamp": int(time.time())
            }

            summary_entry = {
                    "id": counter,
                    "repo_full_name": repo_full,
                    "original_html_url": html_url
                }
            summary = load_summary(summary_path)
            summary.append(summary_entry)
            save_summary_atomic(summary_path, summary)
            print(f"Saved summary entry id {counter} -> {summary_path}")

            # polite sleep and rate-limit checking
            time.sleep(sleep_between)
            # check remaining rate-limit if header present
            try:
                rem = resp_headers.get("X-RateLimit-Remaining")
                reset_ts = resp_headers.get("X-RateLimit-Reset")
                if rem is not None:
                    rem_i = int(rem)
                    if rem_i < 5:
                        reset_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(reset_ts))) if reset_ts else "unknown"
                        print(f"Warning: low search rate limit remaining: {rem_i}. Next reset at {reset_time}. Stopping further search pages.")
                        return
            except Exception:
                pass

        # pagination end condition: less than per_page items
        # if len(items) < per_page:
        #     print("Last search page reached (less than per_page).")
        #     break

        page += 1

    print("\nFinished search & download.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", "-t", required=True, help="GitHub Personal Access Token")
    p.add_argument("--query", "-q", required=True, help="GitHub 搜索关键字, e.g. \"template <script> language:vue\"")
    p.add_argument("--output-dir", "-o", default="downloaded", help="保存的下载路径")
    p.add_argument("--summary", default="summary.json", help="github文件索引")
    p.add_argument("--per-page", type=int, default=100, help="results per search page (default 100)")
    p.add_argument("--max-pages", type=int, default=1000, help="max search pages to fetch (safety cap)，默认1000")
    p.add_argument("--sleep", type=float, default=0.3, help="sleep seconds between downloads (politeness)， 默认0.3")
    args = p.parse_args()

    token = args.token.strip()
    if not token:
        print("Error: GitHub Token is required.")
        sys.exit(1)

    print("Starting.")
    print(f"Query: {args.query}")
    print(f"Output dir: {args.output_dir}")

    process_search_and_download(args.query, args.output_dir, args.summary,
                                token, per_page=args.per_page, max_pages=args.max_pages, sleep_between=args.sleep)


if __name__ == "__main__":
    main()
