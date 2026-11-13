"""模拟 Win64 寄存器与注入内存回调的 Shell32 提取核心，不连接真实进程。"""
from collections.abc import Mapping
from dataclasses import dataclass

if __package__:
    from .legacy_source_api_buffers import decode_shell_folder
else:
    from legacy_source_api_buffers import decode_shell_folder

UINT64_MAX = (1 << 64) - 1
_CALLERS = {0xa56bbe: 0x1c, 0xa56bec: 0x1a}


class CallCaptureError(ValueError):
    """调用字段、地址或回调结果不符合冻结契约。"""


def _integer(value, name, minimum=0, maximum=UINT64_MAX):
    if type(value) is not int or not minimum <= value <= maximum:
        raise CallCaptureError(name + '必须是范围内的精确整数，拒绝布尔和浮点')
    return value


def _registers(registers, expected):
    if not isinstance(registers, Mapping) or set(registers) != set(expected):
        raise CallCaptureError('寄存器字段须恰含：' + ', '.join(expected))
    # 在任何回调前复制纯整数，后续不再引用调用者的映射。
    return {name: _integer(registers[name], name) for name in expected}


def _range(address, size, name):
    _integer(address, name, 1)
    if address + size > UINT64_MAX:
        raise CallCaptureError(name + '加读取长度会发生无符号 64 位溢出')


def _read(read_memory, address, size):
    if not callable(read_memory):
        raise CallCaptureError('read_memory必须是显式提供的可调用对象')
    # 异常原样向上传递，不重试、不补齐或构造成功结果。
    result = read_memory(address, size)
    if not isinstance(result, Mapping) or set(result) != {'data', 'complete'}:
        raise CallCaptureError('内存回调结果须恰含data和complete')
    data, complete = result['data'], result['complete']
    if type(data) is not bytes or type(complete) is not bool:
        raise CallCaptureError('内存回调data必须为bytes，complete必须为bool')
    if len(data) > size:
        raise CallCaptureError('内存回调返回字节数超过请求，拒绝截断修补')
    return data, complete


@dataclass(frozen=True, slots=True)
class _ShellFolderEntry:
    """只保存不可变标量，不保存输入字典或内存回调。"""
    module_base: int
    caller_rva: int
    entry_rsp: int
    return_address: int
    hwnd: int
    buffer_address: int
    csidl: int
    f_create: int
    read_limit: int
    encoding: str


def _parameters(module_base, caller_rva, entry_rsp, hwnd, buffer_address,
                csidl, f_create, read_limit, encoding):
    _integer(module_base, 'module_base', 1)
    _integer(caller_rva, 'caller_rva')
    if caller_rva not in _CALLERS or module_base + caller_rva > UINT64_MAX:
        raise CallCaptureError('caller_rva不在冻结调用点内或模块地址相加溢出')
    _integer(read_limit, 'read_limit', 1, 0x104)
    _range(entry_rsp, 8, 'entry_rsp')
    _range(buffer_address, read_limit, 'buffer_address')
    if type(hwnd) is not int or hwnd != 0:
        raise CallCaptureError('已核调用仅接受hwnd为精确整数0')
    if type(csidl) is not int or csidl != _CALLERS[caller_rva]:
        raise CallCaptureError('R8D的CSIDL与冻结caller_rva不匹配')
    if type(f_create) is not int or f_create != 0:
        raise CallCaptureError('已核调用仅接受R9D为0')
    if type(encoding) is not str:
        raise CallCaptureError('encoding必须是调用者显式提供的编码名称')
    # 只复用公共解码器验证格式和编码，空输入不作为观测结果发布。
    decode_shell_folder(raw_bool=0, raw_bytes=b'', read_limit=read_limit,
                        read_complete=False, encoding=encoding)


def begin_shell_folder_call(registers, *, module_base, caller_rva, encoding,
                            read_memory, read_limit=0x104):
    """验证进入参数，仅完整读取RSP处返回地址，返回不可变的局部调用状态。"""
    values = _registers(registers, ('rcx', 'rdx', 'r8', 'r9', 'rsp'))
    csidl, f_create = values['r8'] & 0xffffffff, values['r9'] & 0xffffffff
    _parameters(module_base, caller_rva, values['rsp'], values['rcx'], values['rdx'],
                csidl, f_create, read_limit, encoding)
    data, complete = _read(read_memory, values['rsp'], 8)
    if not complete or len(data) != 8:
        raise CallCaptureError('返回地址读取必须完整且恰为8字节')
    return_address = int.from_bytes(data, 'little')
    _integer(return_address, 'return_address', 1)
    return _ShellFolderEntry(module_base, caller_rva, values['rsp'], return_address,
                             values['rcx'], values['rdx'], csidl, f_create,
                             read_limit, encoding)


def finish_shell_folder_call(entry, registers, *, read_memory):
    """先核返回位置再读保存的进入RDX；输出恰为共同capture对象。"""
    if type(entry) is not _ShellFolderEntry:
        raise CallCaptureError('entry必须是begin返回的不可变调用状态')
    values = _registers(registers, ('rax', 'rip', 'rsp'))
    _parameters(entry.module_base, entry.caller_rva, entry.entry_rsp, entry.hwnd,
                entry.buffer_address, entry.csidl, entry.f_create, entry.read_limit,
                entry.encoding)
    _integer(entry.return_address, 'return_address', 1)
    if values['rip'] != entry.return_address or values['rsp'] != entry.entry_rsp + 8:
        raise CallCaptureError('返回RIP或RSP与保存的调用状态不匹配')
    data, complete = _read(read_memory, entry.buffer_address, entry.read_limit)
    low = values['rax'] & 0xffffffff
    raw_bool = low - (1 << 32) if low & (1 << 31) else low
    # 保留失败残留、短读和解码unknown；实际接受规则交审计器处理。
    decode_shell_folder(raw_bool=raw_bool, raw_bytes=data, read_limit=entry.read_limit,
                        read_complete=complete, encoding=entry.encoding)
    return {
        'api': 'SHGetSpecialFolderPathA', 'module_base': entry.module_base,
        'caller_rva': entry.caller_rva, 'entry_rsp': entry.entry_rsp,
        'return_address': entry.return_address, 'hwnd': entry.hwnd,
        'buffer_address': entry.buffer_address, 'csidl': entry.csidl,
        'f_create': entry.f_create, 'raw_bool': raw_bool, 'raw_hex': data.hex(),
        'read_limit': entry.read_limit, 'read_complete': complete,
        'encoding': entry.encoding,
    }
