"""新归档图片任务的顺序计时器；不访问桌面，不启动产品，不授予现场许可。"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil

from async_product_client.core import Clock, Context, SECOND, digest, require
from async_product_client.review import PiReadVerifier, wall_ns


@dataclass(frozen=True)
class ArchiveImage:
    path: str
    sha256: str


@dataclass(frozen=True)
class ArchiveRequest:
    context: Context
    snapshot: ArchiveImage
    created_wall_ns: int


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def exclusive(path, value):
    with Path(path).open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.flush()
        import os
        os.fsync(out.fileno())


def preflight(bundle_root, *, context, session_file):
    """统一用Python显式UTF-8核对；不得以空集合all()视作冻结通过。"""
    root = Path(bundle_root).resolve()
    manifest = load(root / 'bundle-manifest.json')
    expected = manifest.get('files', {})
    require(expected and isinstance(expected, dict), '冻结清单为空或无效')
    frozen = root / 'frozen'
    paths = list(frozen.rglob('*'))
    require(not any(p.is_symlink() for p in paths), '冻结清单不能包含链接')
    actual = {p.relative_to(frozen).as_posix(): digest(p.read_bytes()) for p in paths
              if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')}
    require(actual == expected, '冻结文件集合或摘要不匹配')
    require(Path(session_file).resolve() == Path(manifest['session_file']).resolve(), '预检会话文件不是冻结路径')
    raw = Path(session_file).read_bytes()
    rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    headers = [x for x in rows if x.get('type') == 'session']
    require(len(headers) == 1 and headers[0].get('id') == context.session_id, '本轮原会话header不符')
    assistants = [x for x in rows if x.get('message', {}).get('role') == 'assistant']
    require(assistants and all((x['message'].get('provider'), x['message'].get('model'),
                               x['message'].get('thinkingLevel')) ==
                              (context.provider, context.model, context.thinking) for x in assistants),
            '缺少实际assistant身份或模型/推理强度不符')
    result = dict(context=asdict(context), frozen_files=len(actual), all_matched=True,
                  assistant_records=len(assistants), session_prefix_sha256=digest(raw),
                  session_prefix_bytes=len(raw), ready_for_live=False, product_launches=0, desktop_requests=0)
    exclusive(root / 'preflight.json', result)
    return result


def initialize(root, *, context, session_file, images):
    root = Path(root).resolve()
    require(len(images) == 2 and len(set(images)) == 2, '必须是两张不同的归档图')
    require(Path(session_file).is_file(), '必须绑定本轮已经创建的原会话文件')
    session_rows = [json.loads(line) for line in Path(session_file).read_text(encoding='utf-8-sig').splitlines() if line]
    headers = [x for x in session_rows if x.get('type') == 'session']
    require(len(headers) == 1 and headers[0]['id'] == context.session_id, '会话文件不属于本轮上下文')
    root.mkdir(parents=True, exist_ok=False)
    copied = []
    for index, name in enumerate(images, 1):
        source = Path(name).resolve()
        raw = source.read_bytes()
        require(raw.startswith(b'\x89PNG\r\n\x1a\n'), '归档输入必须为PNG原图')
        target = root / f'archive-{index}.png'
        shutil.copyfile(source, target)
        require(digest(target.read_bytes()) == digest(raw), '归档图片复制后改变')
        copied.append(dict(source=str(source), path=str(target), sha256=digest(raw)))
    require(copied[0]['sha256'] != copied[1]['sha256'], '归档图hash不能相同')
    manifest = dict(schema_version=1, context=asdict(context), session_file=str(Path(session_file).resolve()),
                    images=copied, ready_for_live=False, product_launches=0, desktop_requests=0,
                    purpose='archive-read-compatibility-and-observed-timing')
    exclusive(root / 'manifest.json', manifest)
    return manifest


def request(root, index, *, clock=None):
    require(type(index) is int and index in (1, 2), '归档图序号必须为1或2')
    root = Path(root)
    clock = clock or Clock()
    manifest = load(root / 'manifest.json')
    if index == 2:
        require((root / 'ack-1.json').is_file(), '必须完成第一张实际read/ack后才发布第二张request')
    require(not (root / f'ack-{index}.json').exists(), 'ack已存在，不能重复发布request')
    image = manifest['images'][index - 1]
    require(digest(Path(image['path']).read_bytes()) == image['sha256'], '归档图片摘要改变')
    row = dict(index=index, context=manifest['context'], snapshot=dict(path=image['path'], sha256=image['sha256']),
               created_mono_ns=clock.monotonic_ns(), created_wall_ns=clock.wall_ns(), ready_for_live=False)
    exclusive(root / f'request-{index}.json', row)
    # 发布完成时间单独保存；read只能发生在持久化完成之后。
    exclusive(root / f'published-{index}.json', dict(monotonic_ns=clock.monotonic_ns(), wall_ns=clock.wall_ns()))
    return row


def acknowledge(root, index, *, judgment, clock=None):
    root = Path(root)
    clock = clock or Clock()
    require(type(index) is int and index in (1, 2) and isinstance(judgment, str) and judgment.strip(),
            '缺少指定会话实际读图的内容说明')
    manifest = load(root / 'manifest.json')
    row = load(root / f'request-{index}.json')
    published = load(root / f'published-{index}.json')
    require(row['context'] == manifest['context'], '归档request上下文改变')
    require(row['snapshot'] == {k: manifest['images'][index - 1][k] for k in ('path', 'sha256')},
            '归档request图像改变')
    require(not (root / f'ack-{index}.json').exists(), 'ack不可复用')
    journal = Path(manifest['session_file']).read_bytes()
    rows = [json.loads(line) for line in journal.decode('utf-8-sig').splitlines() if line]
    calls = []
    for item in rows:
        message = item.get('message', {})
        if message.get('role') == 'assistant' and wall_ns(item['timestamp']) >= published['wall_ns']:
            for part in message.get('content', []):
                if (part.get('type') == 'toolCall' and part.get('name') == 'read'
                        and part.get('arguments', {}).get('path') == row['snapshot']['path']):
                    calls.append(part['id'])
    require(len(calls) == 1, '本次request缺少唯一实际read调用')
    results = [item for item in rows if item.get('message', {}).get('role') == 'toolResult'
               and item['message'].get('toolCallId') == calls[0]]
    require(len(results) == 1, '实际read回执缺失或重复')
    context = Context(**manifest['context'])
    evidence = ArchiveRequest(context, ArchiveImage(**row['snapshot']), row['created_wall_ns'])
    proof = PiReadVerifier(manifest['session_file'], journal_loader=lambda: journal).verify(evidence, calls[0], results[0]['id'])
    now, wall = clock.monotonic_ns(), clock.wall_ns()
    require(proof['start_wall_ns'] >= published['wall_ns'] and proof['end_wall_ns'] <= wall,
            '实际read早于request发布或回执尚未返回')
    require(now >= published['monotonic_ns'] >= row['created_mono_ns']
            and abs((wall - row['created_wall_ns']) - (now - row['created_mono_ns'])) <= SECOND,
            '归档计时单调时钟倒退或墙钟跳变')
    ack = dict(index=index, proof=proof, judgment=judgment, ack_mono_ns=now, ack_wall_ns=wall,
               request_to_ack_seconds=(now - row['created_mono_ns']) / SECOND, ready_for_live=False)
    exclusive(root / f'ack-{index}.json', ack)
    if index == 2:
        first_request = load(root / 'request-1.json')
        first_ack = load(root / 'ack-1.json')
        total = (now - first_request['created_mono_ns']) / SECOND
        require(first_ack['ack_mono_ns'] <= row['created_mono_ns'], '第二张request早于第一张ack')
        exclusive(root / 'timing-result.json', dict(
            read_1_request_to_ack_seconds=first_ack['request_to_ack_seconds'],
            read_2_request_to_ack_seconds=ack['request_to_ack_seconds'], request_1_to_ack_2_seconds=total,
            observed_t1_under_20=first_ack['request_to_ack_seconds'] < 20,
            observed_t2_under_50=total < 50, ready_for_live=False, gui_verified=False,
            meaning='仅本次归档顺序观察区间，包含模型往返与调度，不是未来时延上界或产品竞争证据'))
    return ack


def main():
    parser = argparse.ArgumentParser(description='全新归档图顺序request/read/ack计时，无桌面/产品入口')
    sub = parser.add_subparsers(dest='command', required=True)
    pre = sub.add_parser('preflight')
    pre.add_argument('--bundle-root', type=Path, required=True)
    pre.add_argument('--context', type=Path, required=True)
    pre.add_argument('--session-file', type=Path, required=True)
    init = sub.add_parser('init')
    init.add_argument('--root', type=Path, required=True)
    init.add_argument('--context', type=Path, required=True)
    init.add_argument('--session-file', type=Path, required=True)
    init.add_argument('--images', type=Path, nargs=2, required=True)
    for name in ('request', 'ack'):
        action = sub.add_parser(name)
        action.add_argument('--root', type=Path, required=True)
        action.add_argument('--index', type=int, choices=(1, 2), required=True)
        if name == 'ack': action.add_argument('--judgment', required=True)
    args = parser.parse_args()
    if args.command == 'preflight':
        result = preflight(args.bundle_root, context=Context(**load(args.context)), session_file=args.session_file)
    elif args.command == 'init':
        result = initialize(args.root, context=Context(**load(args.context)), session_file=args.session_file,
                            images=[str(x) for x in args.images])
    elif args.command == 'request': result = request(args.root, args.index)
    else: result = acknowledge(args.root, args.index, judgment=args.judgment)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
