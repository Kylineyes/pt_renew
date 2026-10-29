"""以基础Python启动只读退出见证器；精确PID握手前不执行目标脚本，不调用桌面。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time
import uuid
import os


def base_python(interpreter=sys.executable):
    """解析venv重定向器实际使用的基础解释器，再验证基础路径没有派生额外PID。"""
    code = "import json,os,sys;print(json.dumps(dict(pid=os.getpid(),base=sys._base_executable)))"
    result = subprocess.run([str(interpreter), '-I', '-S', '-c', code], capture_output=True,
                            text=True, encoding='utf-8', timeout=10, check=True)
    resolved = Path(json.loads(result.stdout)['base']).resolve(strict=True)
    process = subprocess.Popen([str(resolved), '-I', '-S', '-c', code], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding='utf-8')
    stdout, stderr = process.communicate(timeout=10)
    row = json.loads(stdout)
    if process.returncode != 0 or stderr or row['pid'] != process.pid:
        raise RuntimeError('基础解释器仍存在进程重定向或探针失败，不能作为精确见证器')
    return resolved


class WitnessLaunch:
    """保留原Popen和身份回执；只显式放行/等待，不终止进程或自动重启。"""

    def __init__(self, script, evidence_root, *, interpreter=sys.executable, ready_timeout=10):
        self.script = Path(script).resolve(strict=True)
        self.script_sha256 = hashlib.sha256(self.script.read_bytes()).hexdigest()
        self.directory = Path(evidence_root).resolve()/('witness-'+uuid.uuid4().hex)
        self.directory.mkdir(parents=True)
        self.ready_path = self.directory/'identity.json'
        self.release_path = self.directory/'release.json'
        self.interpreter = base_python(interpreter)
        self.released = False
        self.identity = {}
        self.stdout = (self.directory/'stdout.log').open('xb')
        self.stderr = (self.directory/'stderr.log').open('xb')
        try:
            self.process = subprocess.Popen([str(self.interpreter), '-I', '-S', str(Path(__file__).resolve()),
                '--child', '--script', str(self.script), '--sha256', self.script_sha256,
                '--evidence', str(self.directory)], cwd=self.script.parent,
                stdout=self.stdout, stderr=self.stderr,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except BaseException:
            self.stdout.close();self.stderr.close()
            raise
        end = time.monotonic()+ready_timeout
        try:
            self.identity = self._wait_identity(end)
            if (self.identity.get('pid') != self.process.pid or
                    Path(self.identity.get('executable', '')).resolve() != self.interpreter or
                    self.identity.get('script_sha256') != self.script_sha256):
                self._abort('原Popen与实际见证器身份不一致，禁止执行目标脚本')
        except BaseException as error:
            # 初始化已经创建了进程。任何读取/解析/校验异常都必须将原Popen
            # 交还调用方等待；不能因构造函数未返回而丢失进程所有权。
            error.pending_launch = self
            raise

    def _wait_identity(self, deadline):
        """仅重读身份文件，沿原握手截止；不重建进程、不放行目标。"""
        last_error = None
        while time.monotonic() < deadline:
            try:
                return json.loads(self.ready_path.read_text(encoding='utf-8'))
            except (FileNotFoundError, PermissionError) as error:
                last_error = error
            if self.process.poll() is not None:
                break
            time.sleep(.01)
        reason = '没有在原握手截止内读到精确进程身份'
        if last_error is not None:
            reason += '：' + type(last_error).__name__ + ': ' + str(last_error)
        self._abort(reason)


    def _abort(self, reason):
        # 未放行的child在自己的10秒截止后正常退出，父不kill，不遗失原Popen。
        error = RuntimeError(reason)
        error.pending_launch = self
        raise error

    def release(self):
        if self.released or self.process.poll() is not None:
            raise RuntimeError('见证器已放行或退出，禁止重复执行')
        if hashlib.sha256(self.script.read_bytes()).hexdigest() != self.script_sha256:
            self._abort('见证器脚本在握手后变化，禁止放行')
        if time.monotonic() >= self.identity['release_deadline']:
            self._abort('见证器放行期限已过，禁止继续启动')
        temporary = self.release_path.with_suffix('.tmp')
        with temporary.open('x', encoding='utf-8') as out:
            json.dump(dict(pid=self.process.pid, script_sha256=self.script_sha256), out)
        temporary.rename(self.release_path)
        self.released = True

    def wait(self, timeout=None):
        code = self.process.wait(timeout=timeout)
        self.stdout.close();self.stderr.close()
        result = dict(pid=self.process.pid, actual_pid=self.identity.get('pid'), exit_code=code,
                      script_sha256=self.script_sha256, released=self.released, termination_calls=0)
        with (self.directory/'popen-exit.json').open('x', encoding='utf-8') as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
        return result


def child(script, sha256, evidence):
    script, evidence = Path(script), Path(evidence)
    if hashlib.sha256(script.read_bytes()).hexdigest() != sha256:
        raise RuntimeError('子进程目标摘要不符')
    deadline = time.monotonic()+10
    identity = dict(pid=os.getpid(), executable=str(Path(sys.executable).resolve()),
                    script_sha256=sha256, release_deadline=deadline)
    temp = evidence/'identity.tmp'
    with temp.open('x', encoding='utf-8') as out:json.dump(identity, out)
    temp.rename(evidence/'identity.json')
    release = evidence/'release.json'
    while not release.exists() and time.monotonic() < deadline:time.sleep(.01)
    if not release.exists():
        raise RuntimeError('未取得父侧身份核对后的放行，目标脚本未执行')
    approved = json.loads(release.read_text(encoding='utf-8'))
    if (approved != dict(pid=os.getpid(), script_sha256=sha256) or time.monotonic() >= deadline
            or hashlib.sha256(script.read_bytes()).hexdigest() != sha256):
        raise RuntimeError('见证器放行身份、截止或摘要不符')
    # 仅用于标准库证据侧脚本。控制客户端仍须显式使用其冻结venv解释器。
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script)]
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='精确基础Python见证器子进程；不启动桌面或控制服务')
    parser.add_argument('--child', action='store_true', required=True)
    parser.add_argument('--script', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--evidence', required=True)
    args = parser.parse_args()
    child(args.script, args.sha256, args.evidence)
