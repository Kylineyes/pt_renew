"""独立收尾helper的精确生命身份查询边界，使用假kernel32，不查询桌面。"""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'tools/legacy_cleanup_session.py'
spec=importlib.util.spec_from_file_location('legacy_cleanup_session',SOURCE)
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)

class Function:
    def __init__(self,call):self.call=call
    def __call__(self,*args):return self.call(*args)

class IdentityTests(unittest.TestCase):
    def test_original_filetime_integer_and_temporary_handle_always_closed(self):
        expected={'pid':45568,'creation_filetime':134388936662276428,'actual_image':str(SOURCE.resolve())}
        for mismatch in (False,True):
            with self.subTest(mismatch=mismatch):
                closed=[]
                class Kernel:pass
                kernel=Kernel()
                kernel.OpenProcess=Function(lambda *args:777)
                kernel.CloseHandle=Function(lambda handle:closed.append(handle))
                def times(handle,*pointers):
                    pointers[0]._obj.value=expected['creation_filetime']+int(mismatch)
                    return 1
                def image(handle,flags,buf,size):buf.value=expected['actual_image'];return 1
                kernel.GetProcessTimes=Function(times)
                kernel.QueryFullProcessImageNameW=Function(image)
                with patch.object(candidate.ctypes,'WinDLL',return_value=kernel,create=True):
                    if mismatch:
                        with self.assertRaisesRegex(RuntimeError,'创建时间'):candidate.exact_target(expected)
                    else:candidate.exact_target(expected)
                self.assertEqual(closed,[777])
                self.assertEqual(expected['creation_filetime'],134388936662276428)

if __name__=='__main__':unittest.main(verbosity=2)
