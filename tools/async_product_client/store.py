"""新证据目录专用持久化；request/ack独占创建，旧文件一律不覆盖。"""
from dataclasses import asdict
import json
import os
from pathlib import Path

from .core import require


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        (self.root / 'requests').mkdir()
        (self.root / 'acks').mkdir()

    def put(self, folder, ident, row):
        require(ident and all(c.isalnum() or c in '-_' for c in ident), '证据文件ID无效')
        with (self.root / folder / (ident + '.json')).open('x', encoding='utf-8') as out:
            json.dump(row, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())

    def request(self, row):
        self.put('requests', row.id, asdict(row))

    def ack(self, ident, row):
        self.put('acks', ident, row)
