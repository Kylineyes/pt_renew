"""在已验Capture候选上最小增加只读配置探针和逐图状态按键。"""
import argparse
import json
from pathlib import Path

from prepare_legacy_capture import prepare_capture
from prepare_legacy_click_observation import replace,sha,REPO


def prepare_state(**arguments):
    prepare_capture(**arguments)
    root=Path(arguments['destination']).resolve();slot=root/'slot'
    driver=(root/'desktop_session.py').read_text(encoding='utf-8')
    gate=(root/'review_gate.py').read_text(encoding='utf-8')
    gate=replace(gate,"('Launch', 'App', 'Snapshot', 'Click')","('Launch', 'App', 'Snapshot', 'Click', 'Shortcut')")
    gate=replace(gate,"    if tool == 'Click' and request.get('purpose')", """    if tool == 'Shortcut':
        allowed={'startup_enter':'enter','information':'shift+i','status':'shift+s','modal_return':'esc'}
        purpose=request.get('purpose')
        if purpose not in allowed or request.get('arguments')!={'shortcut':allowed[purpose]}:
            raise RuntimeError('状态步骤只允许逐图确认的Enter/Information/Status/模态Esc')
        if purpose=='modal_return':
            if len(list(root.glob('*-modal-return-used.json')))>=2: raise RuntimeError('模态返回最多两次')
        elif (root/(purpose+'-used.json')).exists(): raise RuntimeError('该状态按键已使用，不重发')
    if tool == 'Click' and request.get('purpose')""")
    gate=replace(gate,"state.get('rounds_completed', 0) >= 2", "state.get('rounds_completed', 0) >= 6")
    gate=replace(gate,"两轮已完成，只允许正常收尾","六次客体证据预算已满，只允许正常收尾")
    driver=replace(driver,"                rpc.tool(tool, args, name)\n                interval = rpc.last_interval", """                if tool == 'Shortcut':
                    marker=name+'-modal-return-used.json' if req['purpose']=='modal_return' else req['purpose']+'-used.json'
                    save(marker,{'at':stamp(),'perf_counter_ns':time.perf_counter_ns(),'arguments':args,'note':'发前一次性消费，失败不重发'})
                rpc.tool(tool, args, name)
                interval = rpc.last_interval""")
    (root/'desktop_session.py').write_text(driver,encoding='utf-8')
    for folder in (root,slot):(folder/'review_gate.py').write_text(gate,encoding='utf-8')
    # 只读CONFIG查询在同一已隔离autoexec中先于PT，输出只写本槽runtime根，不碰安装或输入pt目录。
    probes=['config > C:\\CFGINFO.TXT','config -axtype > C:\\AUTOEXEC.TXT',
        'config -get "sdl output" > C:\\OUTPUT.TXT','config -get "dosbox machine" > C:\\MACHINE.TXT',
        'config -get "cpu cycles" > C:\\CYCLES.TXT','config -get "dosbox memsize" > C:\\MEMSIZE.TXT',
        'config -get "dosbox captures" > C:\\CAPTURE.TXT']
    config=(slot/'SYN1.conf').read_text(encoding='utf-8')
    config=replace(config,'c:\ncd \\pt\npt SYN1.PCB','c:\n'+'\n'.join(probes)+'\ncd \\pt\npt SYN1.PCB')
    (slot/'SYN1.conf').write_text(config,encoding='utf-8')
    plan=json.loads((slot/'live-plan.json').read_text(encoding='utf-8'))
    plan.update({'driver_sha256':sha(root/'desktop_session.py'),'review_gate_sha256':sha(root/'review_gate.py'),
        'capture_rounds':6,'executor':'本Pi唯一操作者，逐图核配置和Information/Status，禁止编辑/另存',
        'acceptance':['只读CONFIG来源/autoexec/关键有效值与同次日志','启动页客体read后一次Enter，再依当前图Information/Status及客体文件名计数证据','当前图正常宿主X、原Popen真实wait'],
        'configuration_probes':probes,'configuration_probe_output_root':str(slot/'runtime')})
    plan['target']['configuration_sha256']=sha(slot/'SYN1.conf')
    for item in plan['frozen_files']:item.update({'bytes':Path(item['path']).stat().st_size,'sha256':sha(item['path'])})
    extra=[Path(__file__),Path('C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/languages/en_US.lng'),
        Path('C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.conf'),
        Path('C:/Users/rikideng/AppData/Local/DOSBox-X/dosbox-x-2026.10.01.conf')]
    for p in extra:
        plan['frozen_files'].append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
    (slot/'live-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    preparation=json.loads((root/'preparation.json').read_text(encoding='utf-8'))
    preparation.update({'plan_sha256':sha(slot/'live-plan.json'),'files':plan['frozen_files'],'status_only':True})
    (root/'preparation.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'final_plan_sha256':sha(slot/'live-plan.json'),'driver_sha256':plan['driver_sha256'],'gate_sha256':plan['review_gate_sha256'],'frozen_files':len(plan['frozen_files']),'slot':str(slot)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true')
    for name in ('source','destination','installation','session','task','dispatch'):parser.add_argument('--'+name,required=True)
    prepare_state(**vars(parser.parse_args()))
