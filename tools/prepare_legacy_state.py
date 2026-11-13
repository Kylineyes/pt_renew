"""在已验Capture候选上最小增加只读配置探针和逐图状态按键。"""
import argparse
import json
from pathlib import Path

from prepare_legacy_capture import prepare_capture
from prepare_legacy_click_observation import replace,sha,REPO
from prepare_legacy_navigation import prepare_navigation


def prepare_state(*, named_status=False, budget_seconds=2400, file_submitter_session=None, **arguments):
    if named_status:
        return prepare_named_state(budget_seconds=budget_seconds, file_submitter_session=file_submitter_session, **arguments)
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
    finish_state(root)


def prepare_named_state(*, budget_seconds=3600, file_submitter_session=None, **arguments):
    """仅以已证命名导航及Information首行一次Up进入Status，不使用Shift字母。"""
    if file_submitter_session is None:
        raise ValueError('新命名Status方案必须显式绑定owner投递线程的原Pi JSONL')
    prepare_navigation(budget_seconds=budget_seconds, file_submitter_session=file_submitter_session, **arguments)
    root=Path(arguments['destination']).resolve();slot=root/'slot'
    gate=(root/'review_gate.py').read_text(encoding='utf-8')
    gate=replace(gate,"allowed={'startup_enter':'enter','main_menu_enter':'enter','information_confirm':'enter','navigate_down':'down','navigate_up':'up','menu_return':'esc'}",
        "allowed={'startup_enter':'enter','main_menu_enter':'enter','information_confirm':'enter','navigate_down':'down','status_position':'up','status_confirm':'enter','status_return':'esc','menu_return':'esc'}")
    gate=replace(gate,"limit={'navigate_down':7,'navigate_up':1}.get(purpose,1)","""def used(key): return len(list(root.glob('*-'+key+'-used.json')))
        # 只在已经逐图确认的当前上下文消费专属输入预算，禁止回到旧业务阶段。
        requirements={'main_menu_enter':'startup_enter','navigate_down':'main_menu_enter',
            'information_confirm':'navigate_down','status_position':'information_confirm',
            'status_confirm':'status_position','status_return':'status_confirm','menu_return':'status_return'}
        prerequisite=requirements.get(purpose)
        if prerequisite and not used(prerequisite): raise RuntimeError('命名状态上下文尚未到达')
        if purpose=='information_confirm' and used('navigate_down')!=7:
            raise RuntimeError('主菜单必须逐图完成七次Down，Information当前高亮才确认')
        phases={'startup_enter':0,'main_menu_enter':1,'navigate_down':2,'information_confirm':3,
            'status_position':4,'status_confirm':5,'status_return':6,'menu_return':7}
        if any(used(key) and phase>phases[purpose] for key,phase in phases.items()):
            raise RuntimeError('禁止跨上下文回放已结束阶段')
        limit=7 if purpose=='navigate_down' else 1""")
    gate=replace(gate,"state.get('rounds_completed', 0) >= 14","state.get('rounds_completed', 0) >= 16")
    gate=replace(gate,'十四次逐步客体证据预算已满，只允许正常收尾','十六次状态客体证据预算已满，只允许正常收尾')
    for folder in (root,slot):(folder/'review_gate.py').write_text(gate,encoding='utf-8')
    finish_state(root, named_status=True)


def finish_state(root, *, named_status=False):
    slot=root/'slot'
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
    if named_status:
        plan.update({'capture_rounds':16,
            'executor':'同一原Pi唯一操作者；命名Enter/Down/Up/Enter到Status，只Esc返回，不选择报告输出',
            'navigation_limits':{'startup_enter':1,'main_menu_enter':1,'navigate_down':7,'information_confirm':1,
                'status_position':1,'status_confirm':1,'status_return':1,'menu_return':1},
            'acceptance':['七CONFIG只读探针与同次启动日志核有效值及来源覆盖边界',
                '主菜单七次Down逐图到Information，确认Enter后Board Dimensions首行新guest',
                '仅该首行一次Up，实际新guest明确Status高亮才确认Enter一次',
                'Status新guest实际读Work File Name和八图元计数，只Esc退出并新guest后验',
                '正常宿主X/四原wait及owner文件线程stop/join'],
            'exclusions':['无Shift字母/Unicode字符/IME设置/End或Home定位/低层输入/编辑/保存/EX007',
                'Status页禁止Enter、报告和SAVE FILE NAME；Up后未知不重发或改用六Down',
                'Status的Esc后仅在实际新guest仍有菜单时一次menu_return Esc，否则直接收尾'],
            'status_position_static_basis':{'selector':'324e:19a1..19da','input_code':'0xc8',
                'first_row':1,'visible_rows':7,'last_label':'Status','rule':'Up将当前行减一，为0时改为菜单总项数；实机仍须新guest确认'},
            'remaining_configuration_unknowns':'七探针和单次日志不证明任意多conf优先级或全部潜在来源完整枚举'})
    plan['target']['configuration_sha256']=sha(slot/'SYN1.conf')
    for item in plan['frozen_files']:item.update({'bytes':Path(item['path']).stat().st_size,'sha256':sha(item['path'])})
    extra=[Path(__file__),Path('C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/languages/en_US.lng'),
        Path('C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.conf'),
        Path('C:/Users/rikideng/AppData/Local/DOSBox-X/dosbox-x-2026.10.01.conf')]
    for p in extra:
        plan['frozen_files'].append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
    from legacy_runtime_config import validate_runtime_plan
    plan['isolation_policy'] = validate_runtime_plan(plan)
    (slot/'live-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    preparation=json.loads((root/'preparation.json').read_text(encoding='utf-8'))
    preparation.update({'plan_sha256':sha(slot/'live-plan.json'),'files':plan['frozen_files'],'status_only':True,
        'named_status':named_status})
    (root/'preparation.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'final_plan_sha256':sha(slot/'live-plan.json'),'driver_sha256':plan['driver_sha256'],'gate_sha256':plan['review_gate_sha256'],'frozen_files':len(plan['frozen_files']),'slot':str(slot)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--named-status',action='store_true',help='新方案：命名菜单/首行Up到Status，不使用历史Shift方案')
    parser.add_argument('--budget-seconds',type=int,default=2400,help='新命名方案分段时长，最多3600秒')
    parser.add_argument('--file-submitter-session',help='新命名方案owner文件线程的原Pi JSONL绝对路径')
    parser.add_argument('--refresh',action='store_true')
    for name in ('source','destination','installation','session','task','dispatch'):parser.add_argument('--'+name,required=True)
    prepare_state(**vars(parser.parse_args()))
