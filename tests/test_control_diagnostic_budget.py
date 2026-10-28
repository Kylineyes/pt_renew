"""恢复路径失败后的预算回归：只允许一次诊断和观察，不继续输入探测。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_diagnostic_budget import Budget


class BudgetRecoveryTests(unittest.TestCase):
    def test_failed_restore_allows_one_diagnosis_but_no_input(self):
        b=Budget();b.begin()
        b.restored(dict(completed=False,executed='unknown',reason='Application not found'))
        self.assertTrue(b.refused)
        b.check(dict(kind='diagnose'))
        with self.assertRaises(AssertionError):b.check(dict(kind='diagnose'))
        for tool in ['Click','Shortcut']:
            with self.assertRaises(AssertionError):b.check(dict(kind='action',tool=tool,arguments={}))
        b.check(dict(kind='action',tool='Snapshot'))
        with self.assertRaises(AssertionError):b.check(dict(kind='action',tool='Snapshot'))

    def test_successful_restore_does_not_consume_diagnosis(self):
        b=Budget();b.begin();b.restored(dict(completed=True))
        self.assertFalse(b.refused);self.assertEqual(b.diagnoses,0)
        b.check(dict(kind='action',tool='Snapshot'))

    def test_restore_failure_never_permits_second_group(self):
        b=Budget();b.begin();b.restored(dict(completed=False))
        with self.assertRaises(AssertionError):b.begin()

    def test_cleanup_executed_never_repeats(self):
        b=Budget();b.restored(dict(completed=False))
        r=dict(kind='action',tool='Shortcut',arguments={'shortcut':'alt+f4'})
        b.check(r);b.result(r,dict(completed=False,executed=True,phase='post_native'))
        with self.assertRaises(AssertionError):b.check(r)


if __name__=='__main__':unittest.main(verbosity=2)
