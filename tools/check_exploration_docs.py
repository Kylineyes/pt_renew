"""核验工程探索待办、原文回链和仓库 Markdown 本地链接。只读，不依赖第三方包。"""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / 'docs/exploration-backlog.md'
LINK = re.compile(r'\]\((<[^>]+>|[^)\n]+)\)')
EXPLICIT = re.compile(r'<a\s+id="([^"]+)"\s*></a>')
ITEM = re.compile(r'^### (EX-\d{3,}) (.+)$', re.MULTILINE)
ERRORS: list[str] = []


def outside_code(text: str) -> str:
    """保留位置与换行，排除围栏内的模板和命令示例。"""
    fence = None
    result = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        hidden = fence is not None or marker is not None
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        result.append(re.sub(r'[^\r\n]', ' ', line) if hidden else line)
    return ''.join(result)


def anchors(text: str, path: Path) -> set[str]:
    explicit = EXPLICIT.findall(text)
    for name, count in Counter(explicit).items():
        if count > 1:
            ERRORS.append(f'{path.relative_to(ROOT)}：显式锚点重复 {name}')
    result = set(explicit)
    counts: Counter[str] = Counter()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.MULTILINE):
        heading = re.sub(r'!?\[([^\]]+)\]\([^)]+\)', r'\1', heading)
        heading = re.sub(r'<[^>]+>', '', heading).replace('`', '')
        heading = heading.lower().strip()
        # GitHub 标题锚点删除标点，保留汉字、字母、数字、空白、短横线和下划线。
        slug = ''.join(c for c in heading if c in '-_' or c.isspace()
                       or unicodedata.category(c)[0] in 'LNM')
        slug = slug.replace(' ', '-')
        number = counts[slug]
        counts[slug] += 1
        result.add(f'{slug}-{number}' if number else slug)
    return result


def resolve(source: Path, target: str):
    target = target.strip().strip('<>')
    if not target or re.match(r'^(?:[A-Za-z][\w+.-]*:|/)', target):
        # 本机绝对证据路径与外部网址不属于可移植文档链接核验。
        return None
    filename, _, fragment = target.partition('#')
    # 忽略证据不随 clone 或新工作树分发，不能把本机缺失当仓库断链。
    if '.local-analysis' in Path(unquote(filename).replace('\\', '/')).parts:
        return None
    return ((source.parent / unquote(filename)).resolve() if filename else source,
            unquote(fragment))


def fail(condition: bool, message: str):
    if not condition:
        ERRORS.append(message)


def main() -> int:
    listed = subprocess.check_output(['git', 'ls-files', '--cached', '--others',
                                     '--exclude-standard', '--', '*.md'],
                                    cwd=ROOT, encoding='utf-8').splitlines()
    paths = sorted({ROOT / name for name in listed if (ROOT / name).is_file()})
    texts = {p: outside_code(p.read_text(encoding='utf-8-sig')) for p in paths}
    targets = {p: anchors(text, p) for p, text in texts.items()}
    links_checked = 0
    for path, text in texts.items():
        for match in LINK.finditer(text):
            target = match.group(1)
            resolved = resolve(path, target)
            if resolved is None:
                continue
            dest, fragment = resolved
            links_checked += 1
            fail(dest.exists(), f'{path.relative_to(ROOT)}：文件链接不存在 {target}')
            if dest.exists() and fragment and dest.suffix.lower() == '.md':
                if dest not in targets:
                    targets[dest] = anchors(outside_code(dest.read_text(encoding='utf-8-sig')), dest)
                fail(fragment in targets[dest],
                     f'{path.relative_to(ROOT)}：章节锚点不存在 {target}')

    text = texts[BACKLOG]
    headings = list(ITEM.finditer(text))
    ids = [m.group(1) for m in headings]
    fail(len(ids) == len(set(ids)), '待办编号重复')
    bodies = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        bodies[heading.group(1)] = text[heading.end():end]
    dependencies = {}
    source_details = 0
    for item_id, body in bodies.items():
        anchor = item_id.lower()
        fail(f'<a id="{anchor}"></a>' in text, f'{item_id} 缺固定事项锚点')
        # 末项正文也可能包含后续通用小节；必填字段只核验本项开头。
        body = re.split(r'^## ', body, maxsplit=1, flags=re.MULTILINE)[0]
        for field in ('状态', '类型', '原文细节', '已知', '要回答', '完成条件'):
            fail(len(re.findall(rf'^- {field}：', body, re.MULTILINE)) == 1,
                 f'{item_id} 的 {field} 字段缺失或重复')
        state = re.search(r'^- 状态：(.*)$', body, re.MULTILINE)
        if state:
            fail(state.group(1).split('；')[0] in ('待领取', '研究中', '受阻'),
                 f'{item_id} 状态非法，完成事项应删除')
            for field in ('负责人', '分支', '会话／证据'):
                fail(field + '：' in state.group(1), f'{item_id} 缺领取字段 {field}')
            if state.group(1).startswith(('研究中', '受阻')):
                fail('负责人：无' not in state.group(1) and '分支：无' not in state.group(1),
                     f'{item_id} 已领取但没有负责人或分支')
        dep_line = re.search(r'^- 类型：(.*)$', body, re.MULTILINE)
        deps = re.findall(r'\]\(#(ex-\d+)\)', dep_line.group(1)) if dep_line else []
        dependencies[item_id] = [dep.upper() for dep in deps]
        for dep in dependencies[item_id]:
            fail(dep in bodies and dep != item_id, f'{item_id} 依赖无效 {dep}')
        source_line = re.search(r'^- 原文细节：(.*)$', body, re.MULTILINE)
        sources = LINK.findall(source_line.group(1)) if source_line else []
        fail(bool(sources), f'{item_id} 没有原文细节链接')
        for target in sources:
            resolved = resolve(BACKLOG, target)
            if resolved is None:
                ERRORS.append(f'{item_id} 原文细节须使用仓库相对链接 {target}')
                continue
            dest, fragment = resolved
            fail(bool(fragment) and dest != BACKLOG, f'{item_id} 原文未指向具体段落 {target}')
            if dest not in texts or not fragment:
                ERRORS.append(f'{item_id} 原文不属于仓库 Markdown {target}')
                continue
            source_details += 1
            source_text = texts[dest]
            match = re.search(r'<a\s+id="' + re.escape(fragment) + r'"\s*></a>', source_text)
            if not match:
                # 后续允许沿用原报告标题锚点；回链仍须在该标题段落附近。
                for heading in re.finditer(r'^#{1,6}\s+.+$', source_text, re.MULTILINE):
                    if fragment in anchors(heading.group(), dest):
                        match = heading
                        break
            fail(match is not None, f'{item_id} 找不到原文锚点 {target}')
            if match:
                start = source_text.rfind('\n', 0, match.start()) + 1
                nearby = '\n'.join(source_text[start:].splitlines()[:7])
                back = [resolve(dest, link) for link in LINK.findall(nearby)]
                fail((BACKLOG, anchor) in back, f'{item_id} 原文锚点附近缺回链 {target}')
        index_rows = re.findall(rf'^\| \[{item_id}\]\(#{anchor}\) \|', text, re.MULTILINE)
        fail(len(index_rows) == 1, f'{item_id} 领取索引行缺失或重复')

    indexed_ids = re.findall(r'^\| \[(EX-\d+)\]\(#ex-\d+\) \|', text, re.MULTILINE)
    fail(set(indexed_ids) == set(ids), '领取索引存在已删除或遗漏事项')
    index_path = ROOT / 'docs/reference-index.md'
    excluded = {'README.md', 'usage.md', 'reference-index.md',
                'exploration-backlog.md', 'exploration-workflow.md'}
    reports = [p for p in paths if p.is_relative_to(ROOT / 'docs')
               and not p.is_relative_to(ROOT / 'docs/topics')
               and p.relative_to(ROOT / 'docs').as_posix() not in excluded]
    indexed_reports = Counter()
    for line in texts[index_path].splitlines():
        if line.startswith('- ['):
            for target in LINK.findall(line):
                resolved = resolve(index_path, target)
                if resolved:
                    indexed_reports[resolved[0]] += 1
    for report in reports:
        fail(indexed_reports[report] == 1,
             f'{report.relative_to(ROOT)}：专题报告未在完整资料索引中恰好出现一次')
    visiting, visited = set(), set()

    def visit(item_id):
        if item_id in visiting:
            ERRORS.append(f'事项依赖成环：{item_id}')
            return
        if item_id in visited:
            return
        visiting.add(item_id)
        for dep in dependencies.get(item_id, []):
            visit(dep)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in ids:
        visit(item_id)
    print(json.dumps({'markdown_files_checked': len(paths), 'local_links_checked': links_checked,
                      'open_items': len(ids), 'source_details_checked': source_details,
                      'indexed_reports_checked': len(reports), 'errors': ERRORS}, ensure_ascii=False, indent=2))
    return 1 if ERRORS else 0


if __name__ == '__main__':
    raise SystemExit(main())
