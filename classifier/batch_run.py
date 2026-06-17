#!/usr/bin/env python3
"""
对 classifier/module-list/ 下所有 xlsx 文件批量执行 domain_classifier.py。
在终端打印执行进度。
"""

import subprocess
import sys
import time
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent / "module-list"
CLASSIFIER = Path(__file__).resolve().parent / "domain_classifier.py"


def main():
    files = sorted(MODULE_DIR.glob("*.xlsx"))
    if not files:
        print(f"未在 {MODULE_DIR} 下找到 xlsx 文件")
        return

    total = len(files)
    success = 0
    fail = 0

    print(f"共 {total} 个文件待处理\n")
    print("-" * 60)

    for i, f in enumerate(files, 1):
        print(f"[{i}/{total}] {f.name} ...", end=" ", flush=True)

        t0 = time.time()
        result = subprocess.run(
            [sys.executable, "-u", str(CLASSIFIER), "--xlsx", str(f)],
        )
        elapsed = time.time() - t0

        if result.returncode == 0:
            print(f"✓ 完成 ({elapsed:.1f}s)")
            success += 1
        else:
            print(f"✗ 失败 ({elapsed:.1f}s)")
            fail += 1

    print("-" * 60)
    print(f"\n全部完成：成功 {success} / {total}，失败 {fail}")


if __name__ == "__main__":
    main()
