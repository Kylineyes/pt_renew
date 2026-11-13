"""两键 CONFIG GET 的离线命令数据与精确校验；不启动进程或生成运行配置。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# 仅对应已有静态两参数契约，不推导其它 CONFIG／shell 语法。
QUERY_COMMANDS = (
    ('fulldouble', 'CONFIG -get sdl fulldouble'),
    ('waitonerror', 'CONFIG -get sdl waitonerror'),
)


def _explicit_list(values, label):
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 2:
        raise ValueError(label + '必须是含一至两项的显式列表')
    if any(not isinstance(value, str) for value in values):
        raise ValueError(label + '每项必须是字符串')
    if len(set(values)) != len(values):
        raise ValueError(label + '拒绝重复项')
    return list(values)


def generate_commands(keys):
    """从明确的小写裸键列表生成独立命令，保持顺序，不清理或猜测输入。"""
    keys = _explicit_list(keys, '键列表')
    known = dict(QUERY_COMMANDS)
    if any(key not in known for key in keys):
        raise ValueError('仅接受精确键名 fulldouble 或 waitonerror')
    return [known[key] for key in keys]


def consume_commands(commands):
    """真实离线消费入口：整串精确匹配后返回数据契约，没有执行分支。"""
    commands = _explicit_list(commands, '命令列表')
    known = {command: key for key, command in QUERY_COMMANDS}
    if any(command not in known for command in commands):
        raise ValueError('命令须逐字匹配已审 ASCII 两参数 GET；拒绝其它 shell 语句或变体')
    return {
        'schema_version': 1,
        'scope': '已有静态两参数候选语法的离线数据，不是目标运行或查询回执',
        'keys': [{'section': 'sdl', 'key': known[command]} for command in commands],
        'commands': commands,
        'execution_ready': False,
        'known_effects': {
            'property': '已有正常局部 getter 路径读取查询时当前值，未写回该 Property；不外推其它路径',
            'shell_environment': {
                'variable': 'CONFIG',
                'operation': 'Program::SetEnv',
                'attempts_update': True,
                'caller_checks_result': False,
                'failure_may_remove_old_entry': True,
                'shared_between_queries': True,
            },
            'output': {
                'dos_handle': 1,
                'delivery_verified': False,
                'caller_checks_write_result': False,
            },
        },
        'missing_evidence': [
            {'kind': 'isolation', 'detail': '实际身份、用户根及 OS 拒绝边界的隔离回执'},
            {'kind': 'observation', 'detail': '目录 API 返回、逐阶段解析和 Host I/O 的完整观测回执'},
            {'kind': 'actual_query', 'detail': '两键实际查询、输出送达及 CONFIG 环境前后与 SetEnv 结果'},
            {'kind': 'creator_exit', 'detail': '原创建者持有的 HANDLE 等待、退出和采集收尾见证'},
        ],
        'boundary': '仅离线命令数据；终止、输出捕获及执行时序交未来已审运行器；本工具不裁决 GO',
    }


def contract_from_keys(keys):
    """生成的命令也经过同一精确消费入口；返回全新的契约数据。"""
    return consume_commands(generate_commands(keys))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--key', action='append', help='精确裸键名，可提供一至两次，保持顺序')
    source.add_argument('--commands-json', type=Path, help='显式 UTF-8 JSON 命令数组文件，只读')
    parser.add_argument('--output', type=Path, help='排他新建 JSON 输出；默认 stdout')
    args = parser.parse_args(argv)
    try:
        if args.commands_json is None:
            report = contract_from_keys(args.key)
        else:
            commands = json.loads(args.commands_json.read_bytes().decode('utf-8-sig'))
            report = consume_commands(commands)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if args.output is None:
            sys.stdout.write(payload)
        else:
            # 已有输入、证据及其已有链接都不能被输出覆写。
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(payload)
    except (OSError, ValueError) as error:
        parser.exit(2, '错误：' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
