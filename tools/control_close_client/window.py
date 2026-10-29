"""自建控制诊断窗口及输入回调日志；不调用控制工具或模拟输入。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

TITLE = 'PT Renew 控制诊断试验'


class WindowLog:
    """逐行持久化窗口事件，事件名参数不占用输入kind字段。"""

    def __init__(self, path):
        self.stream = Path(path).open('x', encoding='utf-8')

    def record(self, event_name, **fields):
        row = dict(event=event_name, pid=os.getpid(), monotonic=time.monotonic(),
                   wall=time.time(), **fields)
        self.stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        self.stream.flush()

    def close(self):
        self.stream.close()


class CallbackCounter:
    """只由Tk的按钮command与绑定快捷键回调调用；离线可独立验证记录逻辑。"""

    def __init__(self, log, present):
        self.log, self.present = log, present
        self.counts = {'click': 0, 'shortcut': 0}

    def on_input(self, input_kind):
        if input_kind not in self.counts:
            raise ValueError('未知的诊断输入回调')
        self.counts[input_kind] += 1
        self.present(f'按钮回调：{self.counts["click"]}；快捷键回调：{self.counts["shortcut"]}')
        self.log.record('input-callback', kind=input_kind, counts=dict(self.counts))


def report_callback_error(log, exc_type, exc_value, exc_traceback, stderr=None):
    """保留Tk异常原堆栈，并在窗口日志标记；不会把异常当作成功。"""
    stderr = sys.stderr if stderr is None else stderr
    try:
        log.record('callback-error', exception=exc_type.__name__)
    finally:
        if stderr is not None:
            print('诊断窗口输入回调发生异常：', file=stderr, flush=True)
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=stderr)
            stderr.flush()


def launch_window(executable, script, evidence_root, popen=subprocess.Popen):
    """显式保存子窗输出；只启动自建窗口，不发送输入。"""
    root = Path(evidence_root)
    with (root / 'window-stdout.log').open('xb') as stdout, (root / 'window-stderr.log').open('xb') as stderr:
        return popen([str(executable), '-X', 'utf8', str(script), '--evidence-root', str(root)],
                     cwd=root, env=dict(os.environ, PYTHONUTF8='1'), stdout=stdout, stderr=stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description='自建控制诊断窗口')
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args(argv)
    import tkinter as tk

    log = WindowLog(args.evidence_root / 'window-events.jsonl')
    root = tk.Tk()
    root.title(TITLE)
    root.geometry('900x500+1000+550')
    root.resizable(True, True)
    status = tk.StringVar(value='按钮回调：0；快捷键回调：0')
    counter = CallbackCounter(log, status.set)
    root.report_callback_exception = lambda t, v, tb: report_callback_error(log, t, v, tb)
    tk.Label(root, text=TITLE, font=('Microsoft YaHei UI', 22)).pack(pady=24)
    tk.Label(root, text='仅用于控制工具诊断，不运行产品候选。', font=('Microsoft YaHei UI', 14)).pack()
    tk.Label(root, textvariable=status, font=('Microsoft YaHei UI', 20)).pack(pady=24)
    tk.Button(root, text='诊断按钮（只增加计数）', font=('Microsoft YaHei UI', 16),
              command=lambda: counter.on_input('click')).pack(pady=10, ipadx=15, ipady=10)
    tk.Label(root, text='快捷键：Ctrl+Shift+F8；关闭：Alt+F4或窗口关闭按钮',
             font=('Microsoft YaHei UI', 12)).pack(pady=20)
    root.bind('<Control-Shift-F8>', lambda event: counter.on_input('shortcut'))

    def close():
        log.record('normal-close', counts=dict(counter.counts))
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', close)
    root.after_idle(lambda: log.record('window-ready', counts=dict(counter.counts),
                                      screen=[root.winfo_screenwidth(), root.winfo_screenheight()]))
    try:
        root.mainloop()
        log.record('mainloop-returned', counts=dict(counter.counts))
    finally:
        log.close()


if __name__ == '__main__':
    main()
