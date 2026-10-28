"""以有所有权检查和失败注入的假API验证资源实验模型，不调用Win32。"""
from collections import Counter
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from control_bitmap_surface_model import BitmapSurfaceModel


class FakeApi:
    def __init__(self):
        self.calls=[]
        self.screen=set()
        self.memory={}
        self.bitmaps={}
        self.next_handle=100
        self.failures=Counter()
        self.frames=[]

    def _call(self, name, *args):
        self.calls.append((name,args))
        if self.failures[name]:
            self.failures[name]-=1
            raise OSError('假API失败：'+name)

    def _handle(self):
        self.next_handle+=1
        return self.next_handle

    def acquire_screen(self):
        self._call('GetDC')
        value=self._handle()
        self.screen.add(value)
        return value

    def release_screen(self, value):
        self._call('ReleaseDC',value)
        self.screen.remove(value)

    def create_memory(self, screen):
        self._call('CreateCompatibleDC',screen)
        assert screen in self.screen
        value=self._handle()
        self.memory[value]='原位图'
        return value

    def delete_memory(self, value):
        self._call('DeleteDC',value)
        del self.memory[value]

    def create_bitmap(self, screen, width, height):
        self._call('CreateDIBSection',screen,width,height)
        assert screen in self.screen
        value=self._handle()
        self.bitmaps[value]=None
        return value,value

    def delete_bitmap(self, value):
        self._call('DeleteObject',value)
        assert value not in self.memory.values(), '不能删除仍被选中的位图'
        del self.bitmaps[value]

    def select(self, memory, bitmap):
        self._call('SelectObject',memory,bitmap)
        assert bitmap=='原位图' or bitmap in self.bitmaps
        previous=self.memory[memory]
        self.memory[memory]=bitmap
        return previous

    def copy(self, bits, pixels):
        self._call('memmove',bits,len(pixels))
        self.bitmaps[bits]=pixels

    def update(self, target, screen, memory, width, height, x, y, opacity):
        self._call('UpdateLayeredWindow',target,screen,memory,width,height,x,y,opacity)
        assert screen in self.screen
        pixels=self.bitmaps[self.memory[memory]]
        assert pixels is not None
        self.frames.append((target,width,height,x,y,opacity,pixels))

    def counts(self):
        return Counter(name for name,args in self.calls)


class SurfaceModelTests(unittest.TestCase):
    def make(self, api, **kwargs):
        return BitmapSurfaceModel(api,2,1,b'12345678',target='图层一',**kwargs)

    def assert_balanced(self, api):
        self.assertFalse(api.screen)
        self.assertFalse(api.memory)
        self.assertFalse(api.bitmaps)

    def test_repeated_opacity_and_position_keep_exact_pixels_and_full_upload(self):
        api=FakeApi()
        surface=self.make(api)
        for x,opacity in ((0,255),(10,80),(10,0)):
            surface.present(x,-5,opacity)
        self.assertEqual(api.frames,[('图层一',2,1,x,-5,opacity,b'12345678')
                                     for x,opacity in ((0,255),(10,80),(10,0))])
        surface.close()
        self.assert_balanced(api)
        self.assertEqual(api.counts(),Counter(GetDC=4,ReleaseDC=4,CreateCompatibleDC=1,
                                              CreateDIBSection=1,SelectObject=2,memmove=1,
                                              UpdateLayeredWindow=3,DeleteDC=1,DeleteObject=1))
        calls=len(api.calls)
        surface.close()
        self.assertEqual(len(api.calls),calls)
        with self.assertRaisesRegex(RuntimeError,'退役'): surface.present(0,0,255)

    def test_every_partial_initialization_failure_balances_acquired_resources(self):
        for name in ('GetDC','CreateCompatibleDC','CreateDIBSection','SelectObject','memmove','ReleaseDC'):
            api=FakeApi()
            api.failures[name]=1
            with self.subTest(name=name),self.assertRaisesRegex(OSError,name):
                self.make(api)
            self.assert_balanced(api)

    def test_constructor_cleanup_failure_returns_pending_owner_for_retirement(self):
        class BrokenCopy(FakeApi):
            def copy(self,bits,pixels):
                self.failures.update(memmove=1,SelectObject=1,DeleteDC=1)
                return super().copy(bits,pixels)
        api=BrokenCopy()
        with self.assertRaises(BaseExceptionGroup) as caught:self.make(api)
        pending=caught.exception.pending_surface
        self.assertIs(pending.api,api)
        self.assertTrue(pending.selected)
        self.assertTrue(api.memory)
        self.assertTrue(api.bitmaps)
        self.assertFalse(api.screen)
        with self.assertRaises(RuntimeError):pending.present(0,0,255)
        pending.close()
        self.assert_balanced(api)

    def test_upload_failures_retire_without_fallback_or_reuse(self):
        for name in ('GetDC','UpdateLayeredWindow','ReleaseDC'):
            api=FakeApi()
            surface=self.make(api)
            api.failures[name]=1
            with self.subTest(name=name),self.assertRaisesRegex(OSError,name):
                surface.present(0,0,128)
            self.assert_balanced(api)
            count=len(api.calls)
            with self.assertRaises(RuntimeError): surface.present(0,0,128)
            self.assertEqual(len(api.calls),count)
            self.assertEqual(api.counts()['UpdateLayeredWindow'],0 if name=='GetDC' else 1)

    def test_restore_failure_deletes_dc_before_bitmap_and_reports_error(self):
        api=FakeApi()
        surface=self.make(api)
        api.failures['SelectObject']=1
        with self.assertRaises(BaseExceptionGroup): surface.close()
        self.assert_balanced(api)
        self.assertEqual([name for name,args in api.calls[-3:]],['SelectObject','DeleteDC','DeleteObject'])
        with self.assertRaises(RuntimeError):surface.present(0,0,100)
        surface.close()
        self.assertEqual(surface.state,'closed')

    def test_restore_and_dc_delete_failure_keep_selected_bitmap_for_retry(self):
        api=FakeApi()
        surface=self.make(api)
        api.failures.update(SelectObject=1,DeleteDC=1)
        with self.assertRaises(BaseExceptionGroup): surface.close()
        self.assertEqual(api.counts()['DeleteObject'],0)
        self.assertTrue(surface.selected)
        self.assertEqual(len(api.memory),1)
        self.assertEqual(len(api.bitmaps),1)
        surface.close()
        self.assert_balanced(api)

    def test_independent_cleanup_failures_preserve_only_remaining_handles(self):
        for name in ('DeleteDC','DeleteObject'):
            api=FakeApi()
            surface=self.make(api)
            api.failures[name]=1
            with self.subTest(name=name),self.assertRaises(BaseExceptionGroup):surface.close()
            self.assertFalse(surface.selected)
            surface.close()
            self.assert_balanced(api)
        api=FakeApi()
        surface=self.make(api)
        api.failures.update(UpdateLayeredWindow=1,ReleaseDC=1,DeleteObject=1)
        with self.assertRaises(BaseExceptionGroup) as caught:surface.present(0,0,255)
        self.assertIn('UpdateLayeredWindow',str(caught.exception.exceptions[0]))
        self.assertTrue(api.screen)
        self.assertTrue(api.bitmaps)
        surface.close()
        self.assert_balanced(api)

    def test_wrong_thread_never_calls_backend_even_during_close(self):
        api=FakeApi()
        owner=[1]
        surface=self.make(api,owner_id=lambda:owner[0])
        owner[0]=2
        calls=len(api.calls)
        for action in (lambda:surface.present(0,0,255),surface.close):
            with self.assertRaisesRegex(RuntimeError,'创建线程'):action()
        self.assertEqual(len(api.calls),calls)
        owner[0]=1
        surface.close()
        self.assert_balanced(api)

    def test_rebuild_creates_fresh_resources_even_for_same_size_or_target(self):
        api=FakeApi()
        old=self.make(api)
        old_handles=(old.memory,old.bitmap)
        old.close()
        for width,height,pixels in ((2,1,b'abcdefgh'),(1,2,b'ABCDEFGH')):
            new=BitmapSurfaceModel(api,width,height,pixels,target='图层一')
            self.assertNotEqual((new.memory,new.bitmap),old_handles)
            new.present(0,0,255)
            self.assertEqual(api.frames[-1][-1],pixels)
            new.close()
        self.assert_balanced(api)
        self.assertEqual(api.counts()['CreateDIBSection'],3)

    def test_bad_pixels_and_opacity_rejected_before_any_native_work(self):
        api=FakeApi()
        for width,height,pixels in ((0,1,b''),(1,1,b'x'),(1,1,bytearray(b'1234')),(True,1,b'1234')):
            with self.assertRaises(ValueError):BitmapSurfaceModel(api,width,height,pixels,target='图层')
        self.assertEqual(api.calls,[])
        surface=self.make(api)
        calls=len(api.calls)
        for opacity in (-1,256,True):
            with self.assertRaises(ValueError):surface.present(0,0,opacity)
        self.assertEqual(len(api.calls),calls)
        surface.close()


if __name__=='__main__':
    unittest.main(verbosity=2)
