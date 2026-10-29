"""可信原MCP结果到产品接口的窄适配；默认禁用，不创建连接或控制服务。"""
from __future__ import annotations

import asyncio
import base64
import copy
import json
from pathlib import Path
import re
import struct
import zlib

from .core import SECOND, digest, require
from .review import Snapshot


def png_dimensions(raw):
    """只解析结构/CRC和IHDR尺寸；图像内容仍由指定模型实际read判断。"""
    require(raw.startswith(b'\x89PNG\r\n\x1a\n'), '原工具image不是PNG')
    cursor, size, idat, ended = 8, None, False, False
    while cursor < len(raw):
        require(cursor + 12 <= len(raw), 'PNG块不完整')
        length, kind = struct.unpack('>I4s', raw[cursor:cursor + 8])
        end = cursor + 12 + length
        require(end <= len(raw), 'PNG块长度越界')
        data = raw[cursor + 8:end - 4]
        crc = struct.unpack('>I', raw[end - 4:end])[0]
        require(zlib.crc32(kind + data) & 0xffffffff == crc, 'PNG块CRC不符')
        if size is None:
            require(kind == b'IHDR' and length == 13, 'PNG缺少首个IHDR')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            require(0 < width <= 32768 and 0 < height <= 32768 and width * height <= 100_000_000
                    and compression == filtering == 0 and interlace in (0, 1)
                    and color in (0, 2, 3, 4, 6) and depth in (1, 2, 4, 8, 16), 'PNG尺寸或编码无效')
            size = width, height
        elif kind == b'IHDR':
            raise ValueError('PNG重复IHDR')
        if kind == b'IDAT': idat = True
        if kind == b'IEND':
            require(length == 0 and end == len(raw) and idat, 'PNG结束或像素块不完整')
            ended = True
        cursor = end
    require(ended and size is not None, 'PNG缺少完整结束块')
    return size


def normalize_result(raw, *, tool, arguments):
    require(isinstance(raw, dict) and raw.get('is_error') is False, '原MCP回执失败或未知')
    require('isError' not in raw, '原MCP序列化协议改变，需要重新冻结')
    parts = raw.get('content')
    require(isinstance(parts, list) and parts, '原MCP回执缺少content')
    row = dict(tool=tool, arguments=copy.deepcopy(arguments), is_error=False, text=[], images=[],
               raw_sha256=digest(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode('utf-8')))
    for part in parts:
        require(isinstance(part, dict), '原MCP内容类型未知')
        if part.get('type') == 'text':
            require(isinstance(part.get('text'), str), '原工具文本无效')
            text = part['text']
            require(re.search(r'^\s*(?:Error\b|Failed\b|Exception\b|无法|.*(?:失败|错误))', text, re.I) is None,
                    '原工具正文报告失败')
            row['text'].append(text)
        elif part.get('type') == 'image':
            require(tool == 'Snapshot' and part.get('mime_type') == 'image/png' and 'mimeType' not in part,
                    '原MCP图像类型或序列化字段改变')
            image = base64.b64decode(part['data'], validate=True)
            png_dimensions(image)
            row['images'].append(dict(data=part['data'], mimeType='image/png'))
        else:
            raise ValueError('原MCP回执含未知内容类型')
    require((tool == 'Snapshot' and len(row['images']) == 1)
            or (tool in ('Click', 'Shortcut') and not row['images']), '原工具缺图、多图或输入意外返回图像')
    return row


class McpProductTransport:
    """只接收已冻结连接对象；按原返回对象落盘后规范字段，不接收外部ack伪造回执。"""

    def __init__(self, ledger, connection, evidence_root, *, enabled=False, validate=None, timeout_ns=35 * SECOND):
        self.ledger, self.connection = ledger, connection
        self.root = Path(evidence_root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.enabled = enabled is True
        self.validate = validate
        self.timeout_ns = timeout_ns
        self.number = 0
        self.used = set()
        self.calls = []

    def write(self, name, row):
        with (self.root / name).open('x', encoding='utf-8') as out:
            json.dump(row, out, ensure_ascii=False, indent=2)
            out.flush()

    async def __call__(self, tool, arguments):
        self.ledger.desktop_allowed()
        require(self.enabled and self.validate is not None, '原MCP适配器默认禁用或缺少冻结schema验证器')
        require(tool in ('Snapshot', 'Click', 'Shortcut'), '产品适配器拒绝其他MCP工具入口')
        if tool == 'Shortcut':
            require(arguments in ({'shortcut': 'delete'}, {'shortcut': 'alt+f4'}), '产品适配器拒绝未冻结快捷键')
            require(arguments != {'shortcut': 'alt+f4'} or self.ledger.cleanup_active,
                    'Alt+F4只能属于显式正常收尾请求')
        if tool == 'Click':
            require(set(arguments) == {'loc'} and isinstance(arguments['loc'], list)
                    and len(arguments['loc']) == 2 and all(type(x) is int for x in arguments['loc']),
                    '产品适配器只接受已核验物理坐标的单次左键')
        if tool == 'Snapshot':
            require(set(arguments) == {'use_vision', 'use_annotation', 'use_ui_tree', 'region'}
                    and arguments['use_vision'] is True and arguments['use_annotation'] is False
                    and arguments['use_ui_tree'] is False and isinstance(arguments['region'], list)
                    and len(arguments['region']) == 4 and all(type(x) is int for x in arguments['region'])
                    and arguments['region'][0] < arguments['region'][2]
                    and arguments['region'][1] < arguments['region'][3], 'Snapshot必须冻结明确region和纯图像参数')
        require(type(self.timeout_ns) is int and 0 < self.timeout_ns <= 35 * SECOND, '原工具超时不可扩大')
        self.ledger.time_left(self.timeout_ns)
        args = copy.deepcopy(arguments)
        self.validate(tool, args)
        self.ledger.desktop_allowed()
        self.number += 1
        call_id = f'{self.number:04}-{tool}'
        start_wall = self.ledger.clock.wall_ns()
        start_mono = self.ledger.clock.monotonic_ns()
        event = dict(call_id=call_id, tool=tool, arguments=args, start_wall_ns=start_wall,
                     start_mono_ns=start_mono, attempted=True, returned=False)
        self.calls.append(event)
        self.write(call_id + '-start.json', event)
        try:
            result = await asyncio.wait_for(self.connection.call_tool(tool, args), self.timeout_ns / SECOND)
            event['returned'] = True
            event.update(end_wall_ns=self.ledger.clock.wall_ns(), end_mono_ns=self.ledger.clock.monotonic_ns())
            # 原协议来自冻结MCP对象的model_dump，不采用调用者提交的已规范JSON。
            raw = result.model_dump(mode='json')
            self.write(call_id + '-raw.json', raw)
            row = normalize_result(raw, tool=tool, arguments=args)
            row.update(call_id=call_id, start_wall_ns=start_wall, end_wall_ns=event['end_wall_ns'])
            for index, image in enumerate(row['images']):
                path = self.root / f'{call_id}-{index:02}.png'
                with path.open('xb') as out: out.write(base64.b64decode(image['data'], validate=True))
                image['path'] = str(path.resolve())
            self.ledger.desktop_allowed()
            require(start_mono <= event['end_mono_ns'] < start_mono + self.timeout_ns
                    and abs((event['end_wall_ns'] - start_wall) - (event['end_mono_ns'] - start_mono)) <= SECOND,
                    '原工具调用期间时钟倒退或墙钟跳变')
            self.write(call_id + '-normalized.json', row)
            return row
        except BaseException as error:
            event.update(error=type(error).__name__, reason=str(error))
            raise
        finally:
            self.write(call_id + '-end.json', event)

    async def snapshot(self, target):
        self.ledger.desktop_allowed()
        rect = tuple(target['rect'])
        require(target.get('coordinate_space') == 'physical-desktop-pixels'
                and target.get('thread_context_restored') is True, 'Snapshot必须绑定已核验物理rect')
        arguments = dict(use_vision=True, use_annotation=False, use_ui_tree=False, region=list(rect))
        row = await self('Snapshot', arguments)
        require(row['call_id'] not in self.used, 'Snapshot原调用已消费')
        image = row['images'][0]
        raw = Path(image['path']).read_bytes()
        width, height = png_dimensions(raw)
        # 必须明确region；全桌面图不能按目标窗口尺寸静默换算坐标。
        text = '\n'.join(row['text'])
        region = re.findall(r'Screenshot Region:\s*\((-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\)', text)
        require(len(region) == 1 and tuple(map(int, region[0])) == rect
                and 'Coordinate Space: Virtual desktop coordinates' in text,
                '原Snapshot回执region或坐标空间与目标物理rect不符')
        self.used.add(row['call_id'])
        shot = Snapshot(image['path'], digest(raw), row['call_id'], row['start_wall_ns'], row['end_wall_ns'],
                        width, height, rect, ((rect[2] - rect[0]) / width, (rect[3] - rect[1]) / height),
                        target['hwnd'], row)
        shot.validate(lambda path: Path(path).read_bytes())
        return shot
