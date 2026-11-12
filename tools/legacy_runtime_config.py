"""隔离 DOSBox 小配置的语义生成和启动预检；仅文件操作，不加载 DLL 或创建进程。"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re

# 严格支持当前已审小配置；未知章节/命令须另行扩展和审查。
KEYS = {'log': {'logfile', 'files', 'exec', 'gui', 'misc'},
        'sdl': {'fullscreen', 'output', 'autolock', 'windowposition', 'showmenu'},
        'dosbox': {'machine', 'memsize', 'fastbioslogo', 'quit warning', 'captures'},
        'cpu': {'core', 'cycles'}, 'mixer': {'nosound'}}
PROBES = {'config': 'CFGINFO.TXT', 'config -axtype': 'AUTOEXEC.TXT',
          'config -get "sdl output"': 'OUTPUT.TXT', 'config -get "dosbox machine"': 'MACHINE.TXT',
          'config -get "cpu cycles"': 'CYCLES.TXT', 'config -get "dosbox memsize"': 'MEMSIZE.TXT',
          'config -get "dosbox captures"': 'CAPTURE.TXT'}


def lexical(path):
    """保留逻辑路径供归属检查；不能先 resolve 抹掉别名来源。"""
    return Path(os.path.abspath(path))


def path_key(path):
    return ntpath.normcase(ntpath.normpath(str(path).replace('/', '\\')))


def same_path(actual, expected):
    return path_key(actual) == path_key(expected)


def require_path(actual, expected):
    raw = str(actual)
    if not raw or any(c in raw for c in ('%', '\x00', '\n', '\r')) or '..' in raw.replace('\\', '/').split('/'):
        raise ValueError('隔离路径拒绝展开、空字符或父级遍历')
    if not same_path(raw, expected):
        raise ValueError('隔离路径不符：' + raw + '，应为：' + str(expected))


def parse_config(text):
    values, autoexec, section, seen = {}, [], None, set()
    for original in text.splitlines():
        line = original.strip()
        if not line or line.startswith(('#', ';')):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1].strip().lower()
            if section in seen or section not in {*KEYS, 'autoexec'}:
                raise ValueError('拒绝重复或未审章节：' + section)
            seen.add(section)
        elif section == 'autoexec':
            autoexec.append(line)
        elif section in KEYS and '=' in line:
            key, value = (x.strip() for x in line.split('=', 1))
            key = key.lower()
            if key not in KEYS[section] or (section, key) in values:
                raise ValueError('拒绝重复或未审属性：' + str((section, key)))
            values[section, key] = value
        else:
            raise ValueError('未审配置行：' + line)
    if not {('log', 'logfile'), ('dosbox', 'captures')} <= values.keys() or 'autoexec' not in seen:
        raise ValueError('缺少唯一的日志/捕获路径或 autoexec')
    return values, autoexec


def autoexec_parts(lines, slot, probes=()):
    if len(lines) != 6 + len(probes):
        raise ValueError('autoexec 零/多匹配或额外命令')
    if lines[0].lower() != '@echo off':
        raise ValueError('autoexec 首命令不符')
    for index, drive in ((1, 'c'), (2, 'd')):
        match = re.fullmatch(r'mount\s+([cd])\s+"([^"\r\n]+)"', lines[index], re.IGNORECASE)
        if not match or match[1].lower() != drive:
            raise ValueError('挂载零/多匹配或含额外参数')
        require_path(match[2], Path(slot)/'runtime')
    if lines[3].lower() != 'c:' or lines[-2].lower() != 'cd \\pt' or lines[-1].lower() != 'pt syn1.pcb':
        raise ValueError('启动盘/目录/输入不符，拒绝额外输入输出')
    if lines[4:-2] != list(probes):
        raise ValueError('autoexec 探针不在计划中')
    outputs, seen = [], set()
    for command in probes:
        match = re.fullmatch(r'(.+) > C:\\([A-Z0-9]+\.TXT)', command)
        if not match or PROBES.get(match[1]) != match[2] or match[2] in seen:
            raise ValueError('CONFIG 探针或隔离输出零/多匹配')
        seen.add(match[2])
        outputs.append(Path(slot)/'runtime'/match[2])
    return outputs


def validate_config_text(text, slot, probes=()):
    values, lines = parse_config(text)
    require_path(values['log', 'logfile'], Path(slot)/'dosbox-startup.log')
    require_path(values['dosbox', 'captures'], Path(slot)/'captures')
    outputs = autoexec_parts(lines, slot, probes)
    for key, value in values.items():
        if key not in {('log', 'logfile'), ('dosbox', 'captures')} and any(mark in value for mark in ('\\', '/', ':', '%')):
            raise ValueError('未审属性含宿主路径：' + str(key))
    return outputs


def rebind_config(template_text, template_slot, destination_slot):
    """按原计划声明的逻辑槽核模板，重建四个路径，不对已 resolve 根作字符串替换。"""
    values, lines = parse_config(template_text)
    validate_config_text(template_text, template_slot)
    values['log', 'logfile'] = str(Path(destination_slot)/'dosbox-startup.log')
    values['dosbox', 'captures'] = str(Path(destination_slot)/'captures')
    result = []
    for section in KEYS:
        items = [(k, v) for (s, k), v in values.items() if s == section]
        if items:
            result += ['[' + section + ']', *(k + '=' + v for k, v in items)]
    result += ['[autoexec]', '@echo off', f'mount c "{Path(destination_slot) / "runtime"}"',
               f'mount d "{Path(destination_slot) / "runtime"}"', 'c:', 'cd \\pt', 'pt SYN1.PCB']
    text = '\n'.join(result) + '\n'
    validate_config_text(text, destination_slot)
    return text


def reject_link(item):
    stat = item.lstat()
    if item.is_symlink() or item.is_junction() or getattr(stat, 'st_file_attributes', 0) & 0x400:
        raise ValueError('拒绝联接/符号链接/重解析点：' + str(item))
    if item.is_file() and stat.st_nlink != 1:
        raise ValueError('拒绝共享文件内容的硬链接：' + str(item))


def confined(path, boundary):
    path, boundary = lexical(path), lexical(boundary)
    if not path.is_relative_to(boundary):
        raise ValueError('逻辑路径逃逸：' + str(path))
    if not same_path(boundary, boundary.resolve()) or not same_path(path, path.resolve()):
        raise ValueError('逻辑/物理路径不同，拒绝别名或联接：' + str(path))
    if not path.resolve().is_relative_to(boundary.resolve()):
        raise ValueError('物理路径逃逸：' + str(path))
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            reject_link(item)
        if item == boundary:
            break


def check_tree(root):
    confined(root, root)
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in [*folders, *files]:
            reject_link(Path(directory)/name)


def check_frozen(plan):
    seen = set()
    for item in plan['frozen_files']:
        path = lexical(item['path'])
        if str(path) in seen:
            raise ValueError('冻结文件重复')
        seen.add(str(path))
        if path.stat().st_size != item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('冻结文件变化：' + str(path))
    required = [plan['driver'], plan['base_python'], plan['target']['argv'][0], plan['control_entry'],
                str(Path(plan['slot'])/'SYN1.conf'), str(Path(__file__))]
    if 'file_submitter' in plan:
        required.append(str(Path(__file__).with_name('legacy_observation_owner.py')))
    if any(str(lexical(path)) not in seen for path in required):
        raise ValueError('启动入口/隔离校验器/配置未冻结')
    lookup = {str(lexical(item['path'])): item for item in plan['frozen_files']}
    for key, path in [('driver_sha256', plan['driver']), ('review_gate_sha256', str(Path(plan['driver']).parent/'review_gate.py')),
                      ('submit_sha256', str(Path(plan['driver']).parent/'submit.py'))]:
        if lookup.get(str(lexical(path)), {}).get('sha256') != plan[key]:
            raise ValueError('计划摘要字段与冻结入口不一致：' + key)
    if lookup[str(lexical(Path(plan['slot'])/'SYN1.conf'))]['sha256'] != plan['target']['configuration_sha256']:
        raise ValueError('配置摘要字段与冻结配置不一致')
    for actual, key in ((plan['target']['argv'][0], 'executable_sha256'),):
        if lookup[str(lexical(actual))]['sha256'] != plan['target'][key]:
            raise ValueError('目标映像摘要字段不一致')


def validate_launch(plan, slot, driver_path=None):
    package = slot.parent
    require_path(plan['driver'], package/'desktop_session.py')
    if driver_path is not None:
        require_path(driver_path, plan['driver'])
    if plan['launch_argv'] != [plan['base_python'], '-B', plan['driver'], str(slot)]:
        raise ValueError('launch_argv 的 Python/driver/ROOT 与计划不符')
    target = plan['target']
    if len(target['argv']) != 3 or target['argv'][1] != '-conf':
        raise ValueError('只允许唯一显式 -conf，不接受额外配置/执行参数')
    for actual, expected in [(target['argv'][2], slot/'SYN1.conf'), (target['cwd'], slot/'runtime/pt'),
                             (target['input'], slot/'runtime/pt/SYN1.PCB'), (target['output'], slot/'runtime/pt/NEWFT.PCB')]:
        require_path(actual, expected)
    # 固定公开 stdio 入口的 AST；不接受任意 -c 命令、serve 参数或额外配置。
    argv = plan['control_argv']
    if len(argv) != 6 or argv[:4] != [plan['base_python'], '-I', '-B', '-c'] or argv[5] != 'serve':
        raise ValueError('控制入口参数不符')
    site = str(Path(plan['control_entry']).parent.parent)
    expected = f'import site,runpy;site.addsitedir({site!r});runpy.run_module("windows_mcp",run_name="__main__")'
    if ast.dump(ast.parse(argv[4]), include_attributes=False) != ast.dump(ast.parse(expected), include_attributes=False):
        raise ValueError('控制入口不是冻结的 windows_mcp stdio 模块')


def target_input_sha(plan):
    return plan['target']['input_sha256']


def validate_runtime_plan(plan, *, runtime_root=None, driver_path=None, check_bytes=True):
    """owner、driver 启动及每个服务/目标创建前执行；摘要不能代语义归属。"""
    slot = lexical(plan['slot'])
    if not slot.is_dir():
        raise ValueError('隔离槽不存在')
    if runtime_root is not None:
        require_path(runtime_root, slot)
    package = slot.parent
    check_tree(package)
    validate_launch(plan, slot, driver_path)
    probes = plan.get('configuration_probes', ())
    outputs = validate_config_text((slot/'SYN1.conf').read_text(encoding='utf-8-sig'), slot, probes)
    if probes:
        require_path(plan['configuration_probe_output_root'], slot/'runtime')
    for name in ('captures', 'inputs', 'runtime/pt'):
        if not (slot/name).is_dir():
            raise ValueError('隔离目录缺失：' + name)
    if not (slot/'runtime/pt/SYN1.PCB').is_file() or (slot/'runtime/pt/TRAXEDIT.DFT').exists():
        raise ValueError('隔离输入或去 DFT 策略不符')
    for field, directory in [('runtime_manifest', slot/'runtime/pt'), ('inputs_manifest', slot/'inputs')]:
        current = {str(path.relative_to(directory)).replace('\\', '/'): {'bytes': path.stat().st_size,
                   'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(directory.rglob('*')) if path.is_file()}
        if current != plan[field]:
            raise ValueError('隔离输入完整集合/大小/摘要变化：' + field)
    if hashlib.sha256((slot/'runtime/pt/SYN1.PCB').read_bytes()).hexdigest() != target_input_sha(plan):
        raise ValueError('计划启动输入摘要不符')
    framework = ['slot/*.json', 'slot/*.jsonl', 'slot/*.png', 'slot/*.bin', 'slot/*.log', 'slot/inbox/', 'slot/service-profile/']
    writes = [slot/'dosbox-startup.log', slot/'captures', slot/'runtime', slot/'inbox', slot/'service-profile', *outputs]
    if 'file_submitter' in plan:
        submitter = plan['file_submitter']
        if not isinstance(submitter, dict) or set(submitter) != {'queue', 'session_file', 'version'} or type(submitter['version']) is not int or submitter['version'] != 1:
            raise ValueError('文件投递线程配置不符')
        require_path(submitter['queue'], slot/'submit-queue')
        session_file = lexical(submitter['session_file'])
        if str(session_file) != submitter['session_file'] or session_file.is_relative_to(package):
            raise ValueError('原Pi JSONL须为候选外的绝对只读来源')
        reject_link(session_file)
        with session_file.open(encoding='utf-8') as stream:
            header = json.loads(stream.readline())
        if header.get('type') != 'session' or header.get('id') != plan['session']:
            raise ValueError('原Pi JSONL会话身份不符')
        framework.append('slot/submit-queue/')
        writes.append(slot/'submit-queue')
    for path in writes:
        confined(path, slot)
    if check_bytes:
        check_frozen(plan)
    return {'slot': str(slot), 'logical_physical_equal': True,
            'framework_writes': framework, 'dos_writes': [str(slot/'runtime'), str(slot/'captures'), str(slot/'dosbox-startup.log')],
            'probe_writes': [str(path) for path in outputs],
            'read_only_sources': [item['path'] for item in plan['frozen_files'] if not lexical(item['path']).is_relative_to(package)] +
                ([plan['file_submitter']['session_file']] if 'file_submitter' in plan else []),
            'limits': '可写范围是本槽及独立复制runtime；拒绝整个候选内的链接/重解析点和多硬链接。不是文件系统沙箱；并发恶意换链的TOCTOU不在证明范围。'}


def validate_plan_file(path, *, driver_path=None):
    path = lexical(path)
    plan = json.loads(path.read_text(encoding='utf-8-sig'))
    return validate_runtime_plan(plan, runtime_root=path.parent, driver_path=driver_path)


def service_environment(slot, original):
    """公开控制包自身缓存/用户目录也限定新槽，不改变系统持久设置。"""
    env = dict(original)
    profile = lexical(slot)/'service-profile'
    for key, child in {'USERPROFILE': 'user', 'APPDATA': 'roaming', 'LOCALAPPDATA': 'local',
                                      'TEMP': 'temp', 'TMP': 'temp', 'XDG_CONFIG_HOME': 'config', 'UV_CACHE_DIR': 'uv-cache',
                       'PYTHONPYCACHEPREFIX': 'pycache'}.items():
        folder = profile/child
        confined(folder, slot)
        folder.mkdir(parents=True, exist_ok=True)
        env[key] = str(folder)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', DO_NOT_TRACK='1', ANONYMIZED_TELEMETRY='false',
               WINDOWS_MCP_SCREENSHOT_BACKEND='pillow')
    return env


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True, help='只读语义预检，不创建服务/目标或修改计划')
    args = parser.parse_args()
    print(json.dumps(validate_plan_file(args.plan), ensure_ascii=False, indent=2))
