"""仅解释调用者提供的目录 API 返回快照；不采集 API、不访问环境或文件。"""
import codecs

MAX_ANSI_BUFFER = 0x104
# 仅允许显式、ASCII 兼容的常见 Windows ANSI 代码页及 UTF-8 代码页。
_ENCODINGS = frozenset({
    'ascii', 'utf-8', 'cp874', 'cp932', 'gbk', 'cp949', 'cp950', 'johab',
    *(f'cp{number}' for number in range(1250, 1259)),
})


class SnapshotFormatError(ValueError):
    """快照字段类型或长度不符合数据契约，拒绝修补输入。"""


def _encoding_name(encoding):
    if not isinstance(encoding, str) or not encoding:
        raise SnapshotFormatError('必须显式提供非空 ANSI 编码名称')
    try:
        name = codecs.lookup(encoding).name
    except LookupError as error:
        raise SnapshotFormatError('未知的显式编码：' + encoding) from error
    if name not in _ENCODINGS:
        raise SnapshotFormatError('不支持该 ANSI 缓冲编码：' + encoding)
    return name


def _buffer(raw_bytes, read_limit, read_complete, encoding, canonical):
    if type(raw_bytes) is not bytes:
        raise SnapshotFormatError('原缓冲必须是 bytes，不接受文本、数组或隐式转换')
    if type(read_limit) is not int or not 1 <= read_limit <= MAX_ANSI_BUFFER:
        raise SnapshotFormatError('读取上限必须是 1 至 0x104 的整数')
    if type(read_complete) is not bool:
        raise SnapshotFormatError('读取完整标志必须是 bool')
    if len(raw_bytes) > read_limit:
        raise SnapshotFormatError('原缓冲长度超过声明的读取上限')
    position = raw_bytes.find(b'\0')
    first_nul = position if position >= 0 else None
    issues = []
    if not read_complete:
        issues.append('incomplete_read')
    if first_nul is None:
        issues.append('missing_nul')
    text = None
    decode_error = None
    if first_nul is not None:
        try:
            # 只解码 C 字符串前缀，尾部仍逐字节保留，不修剪或替换字符。
            text = raw_bytes[:first_nul].decode(canonical, errors='strict')
        except UnicodeDecodeError as error:
            issues.append('decode_error')
            decode_error = {'start': error.start, 'end': error.end, 'reason': error.reason}
    return {
        'raw_bytes': raw_bytes, 'read_limit': read_limit, 'read_complete': read_complete,
        'encoding': encoding, 'canonical_encoding': canonical,
        'first_nul': first_nul, 'text': text,
        'tail_bytes': raw_bytes[first_nul + 1:] if first_nul is not None else None,
        'buffer_status': 'complete' if not issues else 'unknown',
        'possible_truncation': not read_complete or first_nul is None,
        'decode_error': decode_error, 'issues': issues,
    }


def decode_shell_folder(*, raw_bool, raw_bytes, read_limit, read_complete, encoding):
    """解释单次 SHGetSpecialFolderPathA 返回，不推断第二调用或最终来源。

    raw_bool 为原有符号 32 位 BOOL 整数，非零均按成功门解释。
    read_complete 是采集者对本次有界读取完成的声明，不要求填满 read_limit。
    返回中的 text 仅是可解码前缀；只有 path_text 可以作为成功非空返回文本消费。
    """
    if type(raw_bool) is not int or not -(1 << 31) <= raw_bool < (1 << 31):
        raise SnapshotFormatError('原 BOOL 必须是有符号 32 位整数，不能传 Python bool')
    canonical = _encoding_name(encoding)
    result = _buffer(raw_bytes, read_limit, read_complete, encoding, canonical)
    api_success = raw_bool != 0
    complete = result['buffer_status'] == 'complete'
    if not api_success:
        status = 'api_failed'
    elif not complete:
        status = 'unknown'
    else:
        status = 'success_empty' if result['text'] == '' else 'success_nonempty'
    result.update({
        'kind': 'SHGetSpecialFolderPathA', 'raw_bool': raw_bool,
        'api_success': api_success, 'status': status,
        'path_text': result['text'] if status == 'success_nonempty' else None,
        # 仅表示已核局部分支的条件，不表示后继调用已经发生。
        'fallback_required': True if not api_success else (
            result['text'] == '' if complete else None),
    })
    return result


def decode_windir(*, pointer_is_null, raw_bytes, read_limit, read_complete, encoding):
    """解释调用者提供的 windir 查询结果；非 null 空串不走 null 字面后备。"""
    if type(pointer_is_null) is not bool:
        raise SnapshotFormatError('指针 null 标志必须是 bool')
    canonical = _encoding_name(encoding)
    if pointer_is_null:
        if raw_bytes is not None or read_limit is not None or read_complete is not None:
            raise SnapshotFormatError('null 指针不应带缓冲或读取声明，相关字段必须为 None')
        result = {
            'raw_bytes': None, 'read_limit': None, 'read_complete': None,
            'encoding': encoding, 'canonical_encoding': canonical,
            'first_nul': None, 'text': None, 'tail_bytes': None,
            'buffer_status': 'not_applicable', 'possible_truncation': False,
            'decode_error': None, 'issues': [], 'status': 'null_pointer',
        }
    else:
        result = _buffer(raw_bytes, read_limit, read_complete, encoding, canonical)
        result['status'] = 'unknown' if result['buffer_status'] != 'complete' else (
            'nonnull_empty' if result['text'] == '' else 'nonnull_nonempty')
    result.update({
        'kind': 'windir', 'pointer_is_null': pointer_is_null,
        'literal_fallback_required': pointer_is_null,
        'value_text': result['text'] if result['status'] in (
            'nonnull_empty', 'nonnull_nonempty') else None,
    })
    return result
