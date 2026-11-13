"""借用显式HANDLE的Win64有界只读适配；导入和注入构造不加载Windows DLL。"""
import ctypes
import sys

BOOL = ctypes.c_int32
SIZE_T = ctypes.c_uint64
HANDLE = ctypes.c_void_p
ADDRESS = ctypes.c_void_p
UINT64_MAX = (1 << 64) - 1
UINT32_MAX = (1 << 32) - 1
# 排除已知负值伪句柄及其常见错误的32位零扩展形式，不据数值证明实际有效性。
_PSEUDO_HANDLES = frozenset({UINT64_MAX - n for n in range(6)}
                            | {UINT32_MAX - n for n in range(6)})


class MemoryReaderError(ValueError):
    """读取参数或native回执违反固定宽度和有界契约。"""


def _integer(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise MemoryReaderError(name + '必须为范围内的精确整数，拒绝布尔、浮点或字符串')
    return value


def _handle(value):
    _integer(value, 'process_handle', 1, UINT64_MAX)
    if value in _PSEUDO_HANDLES:
        raise MemoryReaderError('不接受无效或伪进程句柄')
    return value


def _abi():
    if ctypes.sizeof(HANDLE) != 8 or ctypes.sizeof(ADDRESS) != 8:
        raise MemoryReaderError('仅支持64位指针宿主的Win64参数约定')
    if ctypes.sizeof(BOOL) != 4 or ctypes.sizeof(SIZE_T) != 8:
        raise MemoryReaderError('BOOL与SIZE_T宽度不符合Win64约定')


class _MemoryReader:
    """串行使用的借用句柄读取器；不拥有或关闭句柄，不管理进程身份。"""
    def __init__(self, process_handle, read_process_memory, get_last_error):
        self._handle = process_handle
        self._read_process_memory = read_process_memory
        self._get_last_error = get_last_error
        self._last_receipt = None
        self._library = None

    @property
    def last_receipt(self):
        """返回最近本次native四字段事实的副本；未完成或异常时不沿用旧成功。"""
        return None if self._last_receipt is None else dict(self._last_receipt)

    def __call__(self, address, size):
        # 包括参数拒绝在内，每次尝试都先清空旧诊断。
        self._last_receipt = None
        _integer(address, 'address', 1, UINT64_MAX)
        _integer(size, 'size', 1, 0x104)
        if address + size > UINT64_MAX:
            raise MemoryReaderError('address加size发生无符号64位溢出')
        local_buffer = (ctypes.c_ubyte * size)()
        # 哨兵可识别native从未写入计数的情况；绝不把初始计数当零读成功。
        transferred = SIZE_T(UINT64_MAX)
        raw_bool = self._read_process_memory(
            HANDLE(self._handle), ADDRESS(address),
            ctypes.cast(local_buffer, ADDRESS), SIZE_T(size), ctypes.pointer(transferred))
        # 失败后先取线程错误码，再解释其它字段；成功不读取陈旧错误码。
        error = self._get_last_error() if type(raw_bool) is int and raw_bool == 0 else None
        _integer(raw_bool, 'native BOOL', -(1 << 31), (1 << 31) - 1)
        if raw_bool == 0:
            _integer(error, 'native error', 0, UINT32_MAX)
        count = transferred.value
        self._last_receipt = {'requested': size, 'transferred': count,
                              'raw_bool': raw_bool, 'error': error}
        if count > size:
            raise MemoryReaderError('native传输计数超出请求或未写入计数，拒绝发布缓冲')
        return {'data': bytes(local_buffer[:count]),
                'complete': raw_bool != 0 and count == size}


def make_memory_reader(process_handle, *, read_process_memory, get_last_error):
    """使用显式注入函数构造回调，不加载DLL、不执行读取或取得句柄。

    注入函数约定：RPM(HANDLE, ADDRESS, ADDRESS, SIZE_T, POINTER(SIZE_T))
    返回由c_int32 restype产生的Python精确整数；get_last_error返回DWORD整数。
    """
    _abi()
    handle = _handle(process_handle)
    if not callable(read_process_memory) or not callable(get_last_error):
        raise MemoryReaderError('RPM和错误码读取必须显式提供可调用对象')
    return _MemoryReader(handle, read_process_memory, get_last_error)


def make_windows_memory_reader(process_handle):
    """未来显式使用的Windows工厂；本轮不调用、不代表真实ABI或权限已验证。"""
    _abi()
    handle = _handle(process_handle)
    if sys.platform != 'win32':
        raise MemoryReaderError('真实工厂仅支持64位Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    rpm = kernel.ReadProcessMemory
    rpm.argtypes = [HANDLE, ADDRESS, ADDRESS, SIZE_T, ctypes.POINTER(SIZE_T)]
    rpm.restype = BOOL
    reader = make_memory_reader(handle, read_process_memory=rpm,
                                get_last_error=ctypes.get_last_error)
    reader._library = kernel
    return reader
