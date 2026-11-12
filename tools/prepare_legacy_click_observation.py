"""从只读旧包生成 EX-001 新候选；不导入驱动、不查询桌面、不启动服务。"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
from legacy_runtime_config import check_tree, confined, lexical, rebind_config, validate_runtime_plan

REPO = Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest(root):
    return {p.relative_to(root).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
            for p in sorted(root.rglob('*')) if p.is_file()}
def dump(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
def replace(text, old, new):
    if text.count(old) != 1: raise RuntimeError('旧驱动边界不唯一：' + old[:100])
    return text.replace(old, new)


def prepare(source, destination, installation, session, task, dispatch, refresh=False):
    destination = lexical(destination)
    confined(destination, REPO / '.local-analysis')
    source, installation = (Path(p).resolve() for p in (source, installation))
    if destination.exists():
        check_tree(destination)
        if not refresh or not (destination/'preparation.json').is_file(): raise FileExistsError(destination)
        if any((destination/'slot'/name).exists() for name in ('go-start.json', 'runner-started.json', 'inbox')):
            raise RuntimeError('已批准或启动的候选不可更新')
    if not destination.is_relative_to(REPO / '.local-analysis'): raise RuntimeError('新候选须位于本树忽略目录')
    oldplan = json.loads((source / 'slot-retry-01/live-plan.json').read_text(encoding='utf-8'))
    template_slot = Path(oldplan['slot'])
    if template_slot.resolve() != (source / 'slot-retry-01').resolve():
        raise RuntimeError('只读模板计划的逻辑槽与实际来源不符')
    conf = rebind_config((source / 'slot-retry-01/SYN1.conf').read_text(encoding='utf-8'), template_slot, destination/'slot')
    before = manifest(installation)
    estimated = sum(v['bytes'] for v in before.values()) + 30 * 1024 * 1024
    if shutil.disk_usage(destination.parent).free < estimated * 3: raise RuntimeError('准备空间不足')
    driver = (source / 'desktop_session.py').read_text(encoding='utf-8')
    if sha(source / 'desktop_session.py') != '7e9f9b6fc29da2e082cbf793d996a46bbd956bed33f46bad979d9099fce4db55':
        raise RuntimeError('不是已审查旧驱动')
    driver = replace(driver, "REPO = Path(r'C:/Users/rikideng/orca/workspaces/pt_renew/review-track-core-boundaries')", f'REPO = Path({str(REPO)!r})')
    driver = replace(driver, 'from inspect_legacy_desktop import inspect_desktop', 'from inspect_legacy_desktop import inspect_desktop\nfrom legacy_click_sampling import SamplingWorker, SamplingJob, require_coverage')
    driver = replace(driver, 'ROOT = Path(sys.argv[1]).resolve()', 'ROOT = Path(os.path.abspath(sys.argv[1]))')
    driver = replace(driver, 'from inspect_legacy_desktop import inspect_desktop', "from legacy_runtime_config import validate_runtime_plan, service_environment\nvalidate_runtime_plan(json.loads((ROOT/'live-plan.json').read_text(encoding='utf-8')), runtime_root=ROOT, driver_path=__file__)\nfrom inspect_legacy_desktop import inspect_desktop")
    driver = replace(driver, 'def main():\n', "def main():\n    initial_plan = json.loads((ROOT/'live-plan.json').read_text(encoding='utf-8'))\n    validate_runtime_plan(initial_plan, runtime_root=ROOT, driver_path=__file__)\n")
    driver = replace(driver, 'def preflight(plan):', 'def preflight(plan):\n    validate_runtime_plan(plan, runtime_root=ROOT, driver_path=__file__)')
    driver = replace(driver, '    def start(self, plan):', '    def start(self, plan):\n        validate_runtime_plan(plan, runtime_root=ROOT, driver_path=__file__)')
    driver = replace(driver, "env = dict(os.environ, PYTHONUTF8='1', DO_NOT_TRACK='1', ANONYMIZED_TELEMETRY='false', WINDOWS_MCP_SCREENSHOT_BACKEND='pillow')", 'env = service_environment(ROOT, os.environ)')
    driver = replace(driver, "                out = (ROOT / (name + '.stdout.bin')).open('xb'); err = (ROOT / (name + '.stderr.bin')).open('xb')\n                if Path(entry['output']).exists(): raise RuntimeError('NEWFT.PCB已存在，禁止覆盖')\n                rpc.remaining()\n                target = subprocess.Popen(entry['argv'], cwd=entry['cwd'], stdout=out, stderr=err); identity = process_identity(target)", """                validate_runtime_plan(plan, runtime_root=ROOT, driver_path=__file__)
                with (ROOT / (name + '.stdout.bin')).open('xb') as out, (ROOT / (name + '.stderr.bin')).open('xb') as err:
                    if Path(entry['output']).exists(): raise RuntimeError('NEWFT.PCB已存在，禁止覆盖')
                    rpc.remaining()
                    validate_runtime_plan(plan, runtime_root=ROOT, driver_path=__file__)
                    target = subprocess.Popen(entry['argv'], cwd=entry['cwd'], stdout=out, stderr=err, env=service_environment(ROOT, os.environ))
                identity = process_identity(target)""")
    driver = replace(driver, "        self.err = (ROOT / 'control-stderr.bin').open('xb'); self.raw = (ROOT / 'control-stdout.jsonl').open('xb')\n        env = service_environment(ROOT, os.environ)\n        self.p = subprocess.Popen(plan['control_argv'], cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, creationflags=subprocess.CREATE_NO_WINDOW)", """        self.err = None; self.raw = None
        try:
            self.err = (ROOT / 'control-stderr.bin').open('xb')
            self.raw = (ROOT / 'control-stdout.jsonl').open('xb')
            env = service_environment(ROOT, os.environ)
            validate_runtime_plan(plan, runtime_root=ROOT, driver_path=__file__)
            self.p = subprocess.Popen(plan['control_argv'], cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, creationflags=subprocess.CREATE_NO_WINDOW)
        except BaseException:
            for stream in (self.raw, self.err):
                if stream is not None: stream.close()
            raise""")
    driver = replace(driver, '    def __init__(self): self.p = None; self.counter = 0; self.messages = queue.Queue(); self.limit = None', '''    def __init__(self):
        self.p = None; self.counter = 0; self.messages = queue.Queue(); self.limit = None
        self.observation_job = None
    def observation_guard(self, *, before_click=False):
        if self.observation_job is not None:
            self.observation_job.guard(require_running=before_click, require_foreground=before_click)
    def desktop_stage(self, action):
        self.observation_guard()
        value = action()
        self.observation_guard()
        return value''')
    driver = replace(driver, 'dict(req, at=stamp())); self.write(req)', "dict(req, at=stamp(), perf_counter_ns=time.perf_counter_ns()))\n        self.observation_guard(before_click=method == 'tools/call' and params.get('name') == 'Click')\n        send_ns = time.perf_counter_ns(); self.write(req)")
    driver = replace(driver, "save(name + '-response.json', dict(msg, at=stamp()))", "receive_ns = time.perf_counter_ns()\n        self.last_interval = (send_ns, receive_ns)\n        save(name + '-response.json', dict(msg, at=stamp(), perf_counter_ns=receive_ns, send_ns=send_ns))")
    driver = replace(driver, '        available = self.remaining()', '        self.observation_guard()\n        available = self.remaining()')
    driver = replace(driver, "        if 'error' in msg: raise Refused(str(msg['error']))", "        self.observation_guard()\n        if 'error' in msg: raise Refused(str(msg['error']))")
    driver = replace(driver, '        native = inspect_desktop(); save(name + \'-native-before.json\', native)', '        native = self.desktop_stage(inspect_desktop); save(name + \'-native-before.json\', native)')
    driver = replace(driver, '        virtual = tuple(ctypes.windll.user32.GetSystemMetrics(i) for i in (76, 77, 78, 79))', '        virtual = tuple(self.desktop_stage(lambda i=i: ctypes.windll.user32.GetSystemMetrics(i)) for i in (76, 77, 78, 79))')
    driver = replace(driver, "save(name + '-images.json', images); save(name + '-native-after.json', inspect_desktop())", "save(name + '-images.json', images); save(name + '-native-after.json', self.desktop_stage(inspect_desktop))")
    driver = replace(driver, "except subprocess.TimeoutExpired: save('control-exit-unproven.json', dict(self.identity, at=stamp()))", "except subprocess.TimeoutExpired:\n            save('control-exit-unproven.json', dict(self.identity, at=stamp()))\n            rc = self.p.wait(); save('control-late-exit.json', dict(self.identity, wait_return=rc, at=stamp()))")
    driver = replace(driver, 'ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))', 'dpi_init_result = bool(ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)))')
    driver = replace(driver, "    save('runner-started.json'", "    save('dpi-init.json', {'result': dpi_init_result, 'note': '仅本驱动进程，不证明服务输入线程DPI'})\n    save('runner-started.json'")
    driver = replace(driver, '    cleanup_notice = False', '    cleanup_notice = False\n    sampler = SamplingWorker()\n    active_job = None\n    cleanup_focus_used = False\n    cleanup_close_used = False')
    driver = replace(driver, '        nonlocal target, identity, root_hwnd', '        nonlocal target, identity, root_hwnd, cleanup_focus_used, cleanup_close_used\n        rpc.observation_job = None')
    driver = replace(driver, "        root_hwnd = guard_window(native, target.pid, root_hwnd, 'Close', req['arguments'])", """        fg = native.get('foreground_after') or {}
        if fg.get('hwnd') != root_hwnd:
            if cleanup_focus_used: raise Refused('本候选只允许一次正常收尾聚焦')
            own = [w for w in native['visible_windows'] if w['hwnd'] == root_hwnd and w['process']['pid'] == target.pid]
            if len(own) != 1: raise Refused('收尾目标精确身份不符')
            focus_args = {'mode': 'switch', 'name': own[0]['title']}
            guard_window(native, target.pid, root_hwnd, 'App', focus_args)
            cleanup_focus_used = True
            rpc.tool('App', focus_args, name+'-cleanup-focus')
            rpc.gate(name+'-after-focus'); rpc.remaining()
            if process_identity(target) != identity: raise Refused('收尾聚焦后原身份变化')
            native = inspect_desktop(); save(name+'-after-focus-native.json', native)
        root_hwnd = guard_window(native, target.pid, root_hwnd, 'Close', req['arguments'])
        if cleanup_close_used: raise Refused('正常关闭已发送，不重复输入')
        cleanup_close_used = True""")
    driver = replace(driver, "                root_hwnd = own[0]['hwnd']; save(name + '-binding.json', dict(identity, hwnd=root_hwnd, at=stamp()))", """                root_hwnd = own[0]['hwnd']; save(name + '-binding.json', dict(identity, hwnd=root_hwnd, at=stamp()))
                left, top, right, bottom = own[0]['rect']
                check = sampler.submit(SamplingJob(ROOT/'compatibility.jsonl', root_hwnd, target.pid,
                    [(left+right)//2, (top+bottom)//2], .35, .01, False))
                active_job = check
                if not check.done.wait(5):
                    check.fail('实机兼容采样结束等待超过5秒'); raise Refused('实机兼容采样未在五秒内真实结束')
                save('compatibility-summary.json', require_coverage(check))
                joined = sampler.close()
                save('compatibility-thread-close.json', {'joined_within_five_seconds': joined, 'at': stamp()})
                if not joined: raise Refused('兼容采样线程未真实结束，禁止菜单动作')
                sampler = SamplingWorker()
                if process_identity(target) != identity: raise Refused('兼容检查后原Popen身份变化')""")
    driver = replace(driver, "                rpc.tool(tool, args, name)\n                last_capture = rpc.snapshot(name + '-post', target.pid)", """                job = None
                if tool == 'Click':
                    save('menu-attempted.json', {'at': stamp(), 'perf_counter_ns': time.perf_counter_ns(), 'name': name})
                    job = sampler.submit(SamplingJob(ROOT/'menu-observation.jsonl', root_hwnd, target.pid,
                        args['loc'], 2, .01, True))
                    active_job = job
                    if not job.ready.wait(.5):
                        job.fail('菜单发送前首样本等待超过0.5秒'); raise Refused('菜单发送前首样本等待超时')
                    rpc.observation_job = job
                    rpc.observation_guard(before_click=True)
                    time.sleep(.05)
                    rpc.observation_guard(before_click=True)
                    native = rpc.desktop_stage(inspect_desktop)
                    save(name+'-immediate-before.json', native)
                    guard_window(native, target.pid, root_hwnd, tool, args)
                    rpc.observation_guard(before_click=True)
                rpc.remaining()
                if process_identity(target) != identity: raise Refused('发送前原Popen身份变化')
                rpc.observation_guard(before_click=tool == 'Click')
                rpc.tool(tool, args, name)
                interval = rpc.last_interval
                rpc.observation_guard()
                last_capture = rpc.snapshot(name + '-post', target.pid)
                if job is not None:
                    if not job.done.wait(4):\n                        job.fail('菜单采样结束等待超过4秒'); raise Refused('菜单采样未真实结束')
                    save('menu-observation-summary.json', require_coverage(job, *interval))
                    if process_identity(target) != identity: raise Refused('菜单后原Popen身份变化')""")
    driver = replace(driver, "            paths = list(inbox.glob('request-*.json'))", """            if (ROOT/'stop-business.json').exists():
                stop = json.loads((ROOT/'stop-business.json').read_text(encoding='utf-8'))
                if any(stop.get(key) != plan[key] for key in ('session','task','dispatch')): raise Refused('停止信号身份不符')
                raise Refused('操作者停止业务：' + str(stop.get('reason')))
            paths = list(inbox.glob('request-*.json'))""")
    driver = replace(driver, "        quiet = time.monotonic() + 120", "        if active_job is not None:\n            active_job.fail('驱动停止业务')\n            save('observer-failure-state.json', {'failure': active_job.failure, 'done': active_job.done.is_set(), 'summary': active_job.summary})\n        rpc.observation_job = None\n        quiet = time.monotonic() + 120")
    driver = replace(driver, '    finally:\n        if target is not None:', "    finally:\n        joined = sampler.close()\n        save('observer-close.json', {'joined_within_five_seconds': joined, 'at': stamp()})\n        if not joined:\n            sampler.thread.join()\n            save('observer-late-close.json', {'joined': True, 'at': stamp()})\n        if target is not None:")
    driver = replace(driver, '                rpc.close(); rpc = None\n                rc = target.wait();', '                rc = target.wait();')
    gate = (source / 'review_gate.py').read_text(encoding='utf-8')
    gate = replace(gate, "    if not isinstance(state, dict):", """    if (root/'menu-attempted.json').exists(): raise RuntimeError('本任务唯一菜单尝试已使用，仅允许正常收尾')
    if tool not in ('Launch', 'App', 'Snapshot', 'Click'): raise RuntimeError('本任务不允许其它业务')
    if tool == 'Click' and request.get('purpose') != 'capture_menu_open': raise RuntimeError('只允许一次菜单打开，不选择截图项')
    if not isinstance(state, dict):""")
    for text in (driver, gate): ast.parse(text)
    if not destination.exists():
        destination.mkdir()
        slot = destination / 'slot'
        (slot / 'inputs').mkdir(parents=True)
        (slot / 'captures').mkdir()
        (slot / 'runtime').mkdir()
        shutil.copytree(installation, slot / 'runtime/pt')
        (slot / 'runtime/pt/TRAXEDIT.DFT').unlink()
        shutil.copy2(source / 'slot-retry-01/inputs/SYN1.PCB', slot / 'inputs/SYN1.PCB')
        shutil.copy2(slot / 'inputs/SYN1.PCB', slot / 'runtime/pt/SYN1.PCB')
    else:
        slot = destination / 'slot'
    if manifest(slot / 'runtime/pt') != oldplan['runtime_manifest'] or manifest(slot / 'inputs') != oldplan['inputs_manifest']:
        raise RuntimeError('全新原安装副本与既有核定输入不一致')
    (destination / 'desktop_session.py').write_text(driver, encoding='utf-8')
    for root in (destination, slot):
        (root / 'review_gate.py').write_text(gate, encoding='utf-8')
        shutil.copy2(source / 'submit.py', root / 'submit.py')
    (slot / 'SYN1.conf').write_text(conf, encoding='utf-8')
    plan = {**oldplan, 'slot': str(slot), 'session': session, 'task': task, 'dispatch': dispatch,
            'driver': str(destination / 'desktop_session.py'), 'driver_sha256': sha(destination / 'desktop_session.py'),
            'review_gate_sha256': sha(destination / 'review_gate.py'), 'submit_sha256': sha(destination / 'submit.py')}
    plan['target'] = {**oldplan['target'], 'argv': [oldplan['target']['argv'][0], '-conf', str(slot / 'SYN1.conf')],
        'cwd': str(slot / 'runtime/pt'), 'input': str(slot / 'runtime/pt/SYN1.PCB'),
        'output': str(slot / 'runtime/pt/NEWFT.PCB'), 'configuration_sha256': sha(slot / 'SYN1.conf')}
    plan['acceptance'] = ['自建目标的只读查询兼容及耗时', '同机perf_counter_ns覆盖一次公开Click及实际菜单后图', '原Popen正常wait及完整输入前后核对']
    plan['stop_rules'] = ['父审阅本候选后写新GO；唯一操作者、唯一目标及单次菜单打开', '拒绝或后验失败即停止，完整120秒零新增桌面请求', '最后七分钟仅正常收尾；原Popen/HANDLE持续持有到真实wait']
    plan['failure_cleanup'] = '静默结束后只接Close/WaitExit/Stop；Close仅可按公开门精确聚焦一次，再正常Alt+F4一次，不能绕门或重发'
    plan['executor'] = '当前Pi worker唯一现场操作者，父已审阅后另写新GO；不选择菜单项'
    plan['launch_argv'] = [plan['base_python'], '-B', str(destination / 'desktop_session.py'), str(slot)]
    if oldplan['control_argv'][1:3] != ['-I', '-c']:
        raise RuntimeError('原公开控制入口不是已审参数')
    plan['control_argv'] = [oldplan['control_argv'][0], '-I', '-B', *oldplan['control_argv'][2:]]
    for key in ('launch_note', 'delivery_note', 'previous_slot_result', 'menu_flow'): plan.pop(key, None)
    paths = [destination / name for name in ('desktop_session.py', 'review_gate.py', 'submit.py')]
    paths += [slot / name for name in ('review_gate.py', 'submit.py', 'SYN1.conf')]
    paths += [REPO / '.gitattributes']
    paths += [REPO / 'tools' / name for name in ('legacy_runtime_config.py', 'observe_legacy_click.py', 'legacy_click_sampling.py', 'legacy_observation_owner.py', 'Start-LegacyObservationOwner.ps1', 'inspect_legacy_desktop.py')]
    # 保留原控制入口等外部冻结项；排除旧启动器及旧工作树路径。
    paths += [Path(item['path']) for item in oldplan['frozen_files'] if not Path(item['path']).is_relative_to(source) and not 'orca\\workspaces' in item['path']]
    site = Path('C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Lib/site-packages/windows_mcp')
    plan['control_entry'] = str(site/'__main__.py')
    paths += [site / name for name in ('__main__.py', 'uia/core.py', 'desktop/service.py', 'tools/input.py', 'uia/enums.py')]
    paths += [Path(plan['base_python']), Path(plan['target']['argv'][0])]
    plan['frozen_files'] = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in dict.fromkeys(paths)]
    for old in (slot/'live-plan.json', destination/'preparation.json'):
        if refresh and old.exists(): old.unlink()
    plan['isolation_policy'] = validate_runtime_plan(plan)
    dump(slot / 'live-plan.json', plan)
    if manifest(installation) != before: raise RuntimeError('原安装发生变化')
    dump(destination / 'preparation.json', {'source_package': str(source), 'installation': str(installation),
        'installation_manifest': before, 'installation_unchanged': True, 'estimated_bytes': estimated,
        'copied_runtime_bytes': sum(v['bytes'] for v in plan['runtime_manifest'].values()),
        'plan_sha256': sha(slot / 'live-plan.json'), 'files': plan['frozen_files']})
    print(json.dumps({'candidate': str(destination), 'plan_sha256': sha(slot / 'live-plan.json'),
                      'runtime_files': len(plan['runtime_manifest']), 'runtime_bytes': sum(v['bytes'] for v in plan['runtime_manifest'].values())}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='只更新尚无GO/现场的自有候选代码；复用已核对运行副本')
    for name in ('source', 'destination', 'installation', 'session', 'task', 'dispatch'): parser.add_argument('--'+name, required=True)
    prepare(**vars(parser.parse_args()))
