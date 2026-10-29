"""本地截图节奏，不请求桌面，不重试工具拒绝。"""
import asyncio,time
class SnapshotPacer:
    def __init__(self,interval=4.0,clock=time.monotonic,sleep=asyncio.sleep):self.interval=interval;self.clock=clock;self.sleep=sleep;self.finished=None
    async def before(self):
        if self.finished is not None:
            remaining=self.finished+self.interval-self.clock()
            if remaining>0:await self.sleep(remaining)
    def after(self):self.finished=self.clock()
