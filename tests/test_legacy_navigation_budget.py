"""分段预算边界回归：原owner/driver最多60分钟，无进程或桌面。"""
import ast
import datetime
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prepare_legacy_navigation as candidate


class NavigationBudgetTests(unittest.TestCase):
    def test_invalid_budget_rejected_before_candidate_generation(self):
        for seconds in (0,420,3601,3900):
            with self.subTest(seconds=seconds), patch.object(candidate,'prepare_capture') as prepare:
                with self.assertRaises(ValueError):candidate.prepare_navigation(budget_seconds=seconds)
                prepare.assert_not_called()

    def test_current_driver_authorize_accepts_sixty_minutes_rejects_sixty_five(self):
        # 函数来源为版本控制准备器引用的已审旧driver，不执行顶层。
        source=Path('C:/Users/rikideng/orca/workspaces/pt_renew/review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/desktop_session.py')
        tree=ast.parse(source.read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='authorize')
        scope={'datetime':datetime}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<原driver authorize纯定义>','exec'),scope)
        binding={'session':'假会话','task':'假任务','dispatch':'假派发'}
        start=datetime.datetime(2026,11,12,3,20,tzinfo=datetime.timezone.utc)
        for seconds,accepted in ((420,False),(421,True),(3600,True),(3900,False)):
            approval={**binding,'start_utc':start.isoformat(),'deadline_utc':(start+datetime.timedelta(seconds=seconds)).isoformat()}
            with self.subTest(seconds=seconds):
                if accepted:
                    end,business=scope['authorize'](binding,approval,start.timestamp())
                    self.assertEqual(end-business,420)
                else:
                    with self.assertRaises(RuntimeError):scope['authorize'](binding,approval,start.timestamp())

    def test_actual_owner_budget_expression_matches_driver_limit(self):
        source=Path(__file__).resolve().parents[1]/'tools/legacy_observation_owner.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        checks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and 'GO时段无效' in ast.unparse(n)]
        node=next(n for n in checks if '420 <' in ast.unparse(n.test))
        expression=compile(ast.Expression(node.test),'<实际owner预算表达式>','eval')
        for seconds,rejected in ((420,True),(421,False),(3600,False),(3900,True)):
            with self.subTest(seconds=seconds):
                self.assertEqual(eval(expression,{'start':1000,'deadline':1000+seconds,'time':type('Clock',(),{'time':staticmethod(lambda:1000)})}),rejected)


if __name__=='__main__':unittest.main(verbosity=2)
