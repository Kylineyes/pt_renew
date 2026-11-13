"""只读比较两个显式提供的冻结配置；仅作文字见证，不模拟 DOSBox 解析器。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ENCODINGS = ('utf-8-sig', 'utf-8', 'utf-16', 'cp437', 'cp1252')
NAME = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_. -]*', re.ASCII)
HEADER = re.compile(r'\[([^\[\]]*)\]', re.ASCII)
UNKNOWN = {
    'type': None, 'legal_values': None, 'effective_value': None,
    'loaded_source': None,
}


def canonical_name(value):
    """只折叠 ASCII 大小写和两端空格／制表符；不推断目标的词法规则。"""
    value = value.strip(' \t')
    if not NAME.fullmatch(value):
        raise ValueError('节名／键名仅支持非空 ASCII 字母数字、下划线、点、横线及内部空格')
    return value.lower()


def candidate_pair(value):
    if value.count('/') != 1:
        raise ValueError('候选须为 SECTION/KEY')
    return tuple(canonical_name(part) for part in value.split('/'))


def validate_candidates(candidates):
    pairs = [tuple(canonical_name(part) for part in pair) for pair in candidates]
    if not 1 <= len(pairs) <= 3 or any(len(pair) != 2 for pair in pairs):
        raise ValueError('必须提供一至三个节／键候选')
    if len(set(pairs)) != len(pairs):
        raise ValueError('拒绝重复候选')
    return pairs


def scan_input(path, candidates, encoding='utf-8-sig'):
    """保留所有匹配行；畸形输入使缺席结论降为未知，不应用 last-wins。"""
    if encoding not in ENCODINGS:
        raise ValueError('不支持的显式编码：' + encoding)
    raw = Path(path).read_bytes()
    report = {
        'path': str(path), 'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(), 'encoding': encoding,
        'scan_complete': False, 'issues': [], 'candidates': [],
    }
    occurrences = {pair: [] for pair in candidates}
    sections = {}

    def issue(line, code, original):
        report['issues'].append({'line': line, 'code': code, 'raw_line': original})

    try:
        text = raw.decode(encoding, errors='strict')
    except UnicodeError as error:
        report['issues'].append({'line': None, 'code': 'decode_error', 'detail': str(error)})
    else:
        report['scan_complete'] = True
        section, section_line = None, None
        # 仅 CRLF、CR、LF 分行；Unicode 分隔符不冒充物理换行。
        for number, original in enumerate(re.split(r'\r\n|\r|\n', text), 1):
            line = original.strip(' \t')
            if any(ord(char) < 32 and char != '\t' or ord(char) == 127
                   or char in '\ufeff\u0085\u2028\u2029' for char in original):
                issue(number, 'unsupported_control', original)
                section, section_line = None, None
                continue
            if not line or line.startswith(('#', ';')):
                continue
            # autoexec 是命令文本：只有完整节头可结束它，含等号的命令也不作属性。
            header = HEADER.fullmatch(line)
            if header:
                try:
                    next_section = canonical_name(header[1])
                except ValueError:
                    if section != 'autoexec':
                        issue(number, 'malformed_section', original)
                        section, section_line = None, None
                    continue
                section = next_section
                section_line = number
                sections.setdefault(section, []).append(number)
                continue
            if section == 'autoexec':
                continue
            if line.startswith('['):
                issue(number, 'malformed_section', original)
                section, section_line = None, None
                continue
            if section is None:
                issue(number, 'outside_section', original)
                continue
            if '=' not in original:
                issue(number, 'non_property_line', original)
                continue
            raw_key, raw_value = original.split('=', 1)
            try:
                key = canonical_name(raw_key)
            except ValueError:
                issue(number, 'malformed_key', original)
                continue
            pair = (section, key)
            if pair in occurrences:
                occurrences[pair].append({
                    'line': number, 'section_line': section_line,
                    'raw_line': original, 'raw_key': raw_key, 'raw_value': raw_value,
                    'value_text': raw_value.strip(' \t'),
                })

    for section, key in candidates:
        items = occurrences[section, key]
        reasons = []
        if section == 'autoexec':
            reasons.append('autoexec_is_command_text')
        if report['issues']:
            reasons.append('input_has_scan_issues')
        if len(sections.get(section, [])) > 1:
            reasons.append('duplicate_section')
        if len(items) > 1:
            reasons.append('duplicate_key')
        status = 'present' if items else ('unknown' if reasons else 'absent')
        report['candidates'].append({
            'section': section, 'key': key, 'section_lines': sections.get(section, []),
            'occurrences': items, 'explicit_override': status,
            'ambiguous': bool(reasons), 'ambiguity_reasons': reasons,
            'unknown': dict(UNKNOWN),
        })
    return report


def inspect_witness(left, right, candidates, *, left_encoding='utf-8-sig',
                    right_encoding='utf-8-sig'):
    pairs = validate_candidates(candidates)
    inputs = [scan_input(left, pairs, left_encoding), scan_input(right, pairs, right_encoding)]
    comparisons = []
    for index, (section, key) in enumerate(pairs):
        a, b = [item['candidates'][index] for item in inputs]
        both_present = bool(a['occurrences'] and b['occurrences'])
        comparable = both_present and not a['ambiguous'] and not b['ambiguous']
        comparisons.append({
            'section': section, 'key': key,
            'raw_value_sequences_equal': (
                [item['raw_value'] for item in a['occurrences']]
                == [item['raw_value'] for item in b['occurrences']]
            ) if both_present else None,
            'single_value_text_equal': (
                a['occurrences'][0]['value_text'] == b['occurrences'][0]['value_text']
            ) if comparable else None,
            'text_distinguishable': (
                a['occurrences'][0]['value_text'] != b['occurrences'][0]['value_text']
            ) if comparable else None,
            'source_attribution': None,
        })
    return {
        'schema_version': 1,
        'scope': '仅调用者提供的两个文件的保守文字扫描；显式覆盖仅指文字出现，不判目标实际覆盖',
        'inputs': inputs, 'input_bytes_equal': inputs[0]['sha256'] == inputs[1]['sha256'],
        'comparisons': comparisons,
        'unknown': dict(UNKNOWN),
        'limitations': [
            '相同值或相同文件摘要不能证明加载来源；不同文字也不能证明实际加载或生效',
            '不模拟 DOSBox 解析器，不应用重复键最后值，不执行 autoexec，不选择合格键或生成配置／GO',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path, help='第一个冻结配置路径')
    parser.add_argument('right', type=Path, help='第二个冻结配置路径')
    parser.add_argument('--candidate', action='append', required=True, help='SECTION/KEY，可重复一至三次')
    parser.add_argument('--left-encoding', choices=ENCODINGS, default='utf-8-sig', help='左输入的显式编码')
    parser.add_argument('--right-encoding', choices=ENCODINGS, default='utf-8-sig', help='右输入的显式编码')
    parser.add_argument('--output', type=Path, help='可选 JSON 路径，必须不存在；默认标准输出')
    args = parser.parse_args(argv)
    try:
        pairs = [candidate_pair(item) for item in args.candidate]
        result = inspect_witness(args.left, args.right, pairs,
                                 left_encoding=args.left_encoding, right_encoding=args.right_encoding)
        payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output is None:
            sys.stdout.write(payload)
        else:
            # 排他创建对已有输入、硬链接、符号链接及证据均拒绝覆写。
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(payload)
    except (OSError, ValueError) as error:
        parser.exit(2, '错误：' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
