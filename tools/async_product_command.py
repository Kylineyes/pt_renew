"""向已审阅的新兼容性客户端提交一条显式命令；本工具不访问桌面。"""
from __future__ import annotations

import argparse
from pathlib import Path

from async_product_client.driver import submit
from async_product_client.events import decode_object


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='提交本轮完整context/id/parent/action/arguments命令，不自动续发或读图')
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    print(submit(args.root, decode_object(args.request.read_bytes())))
