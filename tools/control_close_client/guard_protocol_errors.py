"""识别工具协议中的控制拒绝；普通GUI文字和文件名不当成控制码。"""
import json,re
_CODE=re.compile(r'^(?:USER_CONTROL|CONTROL_[A-Z0-9_]+)$',re.I)
_TOKEN=re.compile(r'\b(?:USER_CONTROL|CONTROL_[A-Z0-9_]+)\b',re.I)
_DIAGNOSTIC=re.compile(r'^\s*(?:error\s*:\s*)?((?:USER_CONTROL|CONTROL_[A-Z0-9_]+))\s*:',re.I)
_LEGACY=re.compile(r'control(?:\s|:).{0,20}(?:unavailable|denied)|用户控制|控制不可用',re.I)
_WRAPPED=frozenset({'error','errors','result','response','data','status','details'})

def _find(value,depth=0):
    if depth>12:return None
    if isinstance(value,dict):
        for key,item in value.items():
            if str(key).casefold() in ('code','error_code') and isinstance(item,str) and _CODE.fullmatch(item.strip()):return item.strip().upper()
        for key,item in value.items():
            if isinstance(item,(dict,list)) or (str(key).casefold() in _WRAPPED and isinstance(item,str)):
                code=_find(item,depth+1)
                if code:return code
    elif isinstance(value,list):
        for item in value:
            code=_find(item,depth+1)
            if code:return code
    elif isinstance(value,str):
        stripped=value.strip()
        if _CODE.fullmatch(stripped):return stripped.upper()
        try:decoded=json.loads(stripped)
        except (ValueError,TypeError):return None
        if decoded!=value:return _find(decoded,depth+1)
    return None

def control_error_code(row):
    code=_find(row.get('structured_content'))
    if code:return code
    for text in row.get('text',[]):
        if not isinstance(text,str):continue
        code=_find(text)
        if code:return code
        diagnostic=_DIAGNOSTIC.match(text)
        if diagnostic:return diagnostic.group(1).upper()
        # is_error为真时，控制诊断可能是未结构化工具错误。
        if row.get('is_error'):
            token=_TOKEN.search(text)
            if token:return token.group(0).upper()
            if _LEGACY.search(text):return 'CONTROL_UNAVAILABLE'
        elif not row.get('images') and _LEGACY.match(text.strip()):return 'CONTROL_UNAVAILABLE'
    return None
