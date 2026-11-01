"""生成基础编辑验收的独立合成输入，不读取原软件或历史证据。"""
from pathlib import Path
import hashlib
import json
import struct
import argparse

parser = argparse.ArgumentParser(description="在全新目录生成基础编辑验收的合成输入与摘要。")
parser.add_argument("output", type=Path, help="尚不存在的输出目录")
root = parser.parse_args().output
root.mkdir(parents=True, exist_ok=False)
board = b"""PCB FILE 4
FT
100 100 400 500 10 1
FT
600 100 900 100 12 6 42
COMP
U1
DIP
Value
0 0 10 0 1 7
0 0 10 0 1 7
0 0 2 2 2
CT
0 0 100 0 10 1
CP
100 100 60 60 1 20 1 13
1
CP
400 500 60 60 1 20 1 13
2
ENDCOMP
ENDPCB
"""
network = b"[\nU1\nDIP\nValue\n\n\n\n]\n(\nGND\nU1-1\nU1-2\n)\n"
files = {"editing.pcb": board, "supported.pcb": board.replace(b"12 6 42\n", b"12 6\n"),
         "empty.pcb": b"PCB FILE 4\nENDPCB\n", "invalid.pcb": b"PCB FILE 4\nUNKNOWN\nENDPCB\n", "editing.net": network}
library = bytearray(6416)
library[:16] = b"\0\0\x0dPCB 4 LIBRARY"
for slot in range(200):
    struct.pack_into("<HH", library, 16 + slot * 32 + 18, 65535, 65535)
name = b"OWN_TEST"
library[18] = len(name)
library[19:19 + len(name)] = name
struct.pack_into("<HH", library, 34, 1, 401)
track = bytearray(16)
track[0:2] = bytes([7, 5])
struct.pack_into("<h", track, 2, -100)
struct.pack_into("<h", track, 6, 100)
struct.pack_into("<h", track, 10, 12)
files["editing.lib"] = bytes(library + track)
for name, data in files.items():
    (root / name).write_bytes(data)
manifest = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in files.items()}
(root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
