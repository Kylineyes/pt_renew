"""隐藏单步驱动；使用唯一参数文件，避免辅助控制台改变前景。"""
from pathlib import Path
import json,sys,traceback
from step import submit
R=Path(__file__).resolve().parent
payload=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
ident=payload['name'];lock=R/'submission.lock'
try:
    with lock.open('x',encoding='utf-8') as f:f.write(ident)
    try:
        row=submit(ident,payload['kind'],payload.get('values') or [])
        (R/(ident+'-driver-result.json')).write_text(json.dumps(row,ensure_ascii=False),encoding='utf-8')
    finally:lock.unlink()
except BaseException:
    (R/(ident+'-driver-error.txt')).write_text(traceback.format_exc(),encoding='utf-8')
    raise SystemExit(1)
