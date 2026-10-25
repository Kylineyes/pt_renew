"""原文字对象创建 32 字符复制边界的推导模型与期望值计算。

说明：本模块只包含从 PT.EXE（SHA-256 见 docs/legacy-text-copy-verification.md）
静态推导的复制规则，用于在没有原二进制的环境下复现期望值并做独立测试；
不含任何原程序字节。受控机器码执行脚本保存在本地
`.local-analysis/text-object-copy/verify_create_copy.py`（被 Git 忽略），
两者结论一致时才允许更新结论。
"""

LOCAL_BUFFER_MAX = 80   # 对象创建先复制到局部缓冲（80 上限）
OBJECT_STORE_MAX = 32   # 再复制到对象 +0x11（32 上限）


def expected_stored_text(text: bytes) -> bytes | None:
    """返回对象内最终保存的短字符串；先 80 截断、去尾部空格、再 32 截断。

    全空格或空串返回 None：原函数不创建对象（实验中 New 分配次数为 0，
    返回值为假）。
    """
    if not isinstance(text, (bytes, bytearray)):
        raise TypeError('输入必须是 bytes')
    if len(text) > 255:
        raise ValueError('Pascal 短字符串长度上限 255')
    local = bytes(text)[:LOCAL_BUFFER_MAX].rstrip(b' ')
    if not local:
        return None
    return local[:OBJECT_STORE_MAX]
