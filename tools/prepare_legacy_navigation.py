"""复用Capture/原wait链，仅增加逐图命名VK菜单导航，不启用Shift字母或编辑。"""
import argparse
import json
from pathlib import Path
from prepare_legacy_capture import prepare_capture
from prepare_legacy_click_observation import replace,sha,REPO


def prepare_navigation(*, budget_seconds=2400, **arguments):
    if not 420 < budget_seconds <= 3600:
        raise ValueError('本入口时段须超过七分钟且不超过六十分钟')
    prepare_capture(**arguments)
    root=Path(arguments['destination']).resolve();slot=root/'slot'
    driver=(root/'desktop_session.py').read_text(encoding='utf-8')
    gate=(root/'review_gate.py').read_text(encoding='utf-8')
    gate=replace(gate,"('Launch', 'App', 'Snapshot', 'Click')","('Launch', 'App', 'Snapshot', 'Click', 'Shortcut')")
    gate=replace(gate,"    if tool == 'Click' and request.get('purpose')",'''    if tool == 'Shortcut':
        allowed={'startup_enter':'enter','main_menu_enter':'enter','information_confirm':'enter','navigate_down':'down','navigate_up':'up','menu_return':'esc'}
        purpose=request.get('purpose')
        if purpose not in allowed or request.get('arguments')!={'shortcut':allowed[purpose]}:
            raise RuntimeError('只允许当前客体图确认的命名Enter/Down/Up/Esc，不许字母或Shift组合')
        limit={'navigate_down':7,'navigate_up':1}.get(purpose,1)
        if len(list(root.glob('*-'+purpose+'-used.json')))>=limit:
            raise RuntimeError('该命名导航输入预算已用完，不重发未知动作')
    if tool == 'Click' and request.get('purpose')''')
    gate=replace(gate,"state.get('rounds_completed', 0) >= 2","state.get('rounds_completed', 0) >= 14")
    gate=replace(gate,'两轮已完成，只允许正常收尾','十四次逐步客体证据预算已满，只允许正常收尾')
    driver=replace(driver,'                rpc.tool(tool, args, name)\n                interval = rpc.last_interval', '''                if tool == 'Shortcut':
                    save(name+'-'+req['purpose']+'-used.json',{'at':stamp(),'perf_counter_ns':time.perf_counter_ns(),'arguments':args,'note':'发前消费；未知响应不重发'})
                rpc.tool(tool, args, name)
                interval = rpc.last_interval''')
    (root/'desktop_session.py').write_text(driver,encoding='utf-8')
    for folder in (root,slot):(folder/'review_gate.py').write_text(gate,encoding='utf-8')
    plan=json.loads((slot/'live-plan.json').read_text(encoding='utf-8'))
    plan.update({'driver_sha256':sha(root/'desktop_session.py'),'review_gate_sha256':sha(root/'review_gate.py'),
        'budget_seconds':budget_seconds,'capture_rounds':14,'executor':'同一指定Pi唯一操作者；逐图命名VK主菜单到Information，不选择任何编辑或写入项',
        'acceptance':['启动客体->一次Enter->板图新guest','主循环一次Enter->主菜单新guest','逐个Down最多7/必要Up最多1且每键新guest确认高亮','仅当前高亮Information时一次Enter->Information新guest；正常X及原wait'],
        'navigation_limits':{'startup_enter':1,'main_menu_enter':1,'information_confirm':1,'navigate_down':7,'navigate_up':1,'menu_return':1},
        'exclusions':['无ShiftI/ShiftS/Unicode字母/IME修改/低层输入','不选Status或其他子项，不吞并EX005/007；Information菜单到达即收尾或单Esc验证返回']})
    for item in plan['frozen_files']:item.update({'bytes':Path(item['path']).stat().st_size,'sha256':sha(item['path'])})
    for p in (Path(__file__),Path('D:/project/pt_renew/pt/TRAXEDIT.MNU'),Path('D:/project/pt_renew/pt/TRAXEDIT.KEY')):
        plan['frozen_files'].append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
    from legacy_runtime_config import validate_runtime_plan
    plan['isolation_policy'] = validate_runtime_plan(plan)
    (slot/'live-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    preparation=json.loads((root/'preparation.json').read_text(encoding='utf-8'))
    preparation.update({'plan_sha256':sha(slot/'live-plan.json'),'files':plan['frozen_files'],'navigation_only':True})
    (root/'preparation.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan_sha256':sha(slot/'live-plan.json'),'driver_sha256':plan['driver_sha256'],'gate_sha256':plan['review_gate_sha256'],'frozen_files':len(plan['frozen_files']),'slot':str(slot)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--budget-seconds',type=int,default=2400,help='完整分段时长，原owner/driver最多3600秒')
    parser.add_argument('--refresh',action='store_true')
    for name in ('source','destination','installation','session','task','dispatch'):parser.add_argument('--'+name,required=True)
    prepare_navigation(**vars(parser.parse_args()))
