"""冻结Windows alpha部署包、许可与校验值；不启动产品或改变旧部署。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.11.0-alpha'
QT_VERSION = '6.12.0'
QT_SOURCE_HASHES = {
    'qtbase': 'a951bd163c7b80fc6b8c88d7668fb56abf91c152373e13c10666763238131307',
    'qtsvg': 'e4ab39534ec97987b1b9b60ef7f4d3253d5912a69f8c713a01753174a4029331',
}


def sha256(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def copy_licenses(archive, target):
    count = 0
    with tarfile.open(archive, 'r:xz') as source:
        for member in source:
            name = PurePosixPath(member.name)
            if not member.isfile() or '..' in name.parts or name.is_absolute():
                continue
            relative = PurePosixPath(*name.parts[1:])
            if not relative.parts:
                continue
            if not ('LICENSES' in relative.parts or re.match(r'^(LICENSE|COPYING|COPYRIGHT|NOTICE)([.\-_].*)?$', relative.name, re.I)):
                continue
            destination = target.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as data, destination.open('xb') as output:
                shutil.copyfileobj(data, output)
            count += 1
    if not count:
        raise ValueError('对应Qt源码未提供许可文件')
    return count


def package(build, output, qt, sources):
    build, output, qt, sources = map(lambda p: Path(p).resolve(), (build, output, qt, sources))
    if output.exists():
        raise ValueError('发布输出必须是全新目录，不能覆盖既有候选')
    for module, expected in QT_SOURCE_HASHES.items():
        archive = sources / f'{module}-everywhere-src-{QT_VERSION}.tar.xz'
        if sha256(archive) != expected:
            raise ValueError('Qt对应源码与官方SHA-256不符：' + module)
    header = (build / 'generated/application/Version.h').read_text(encoding='utf-8')
    if f'"{VERSION}"' not in header:
        raise ValueError('构建版本与发布版本不一致')
    output.mkdir(parents=True)
    stage = output / f'pt-renew-v{VERSION}-windows-x64'
    stage.mkdir()
    executable = stage / 'pt-renew.exe'
    shutil.copyfile(build / executable.name, executable)
    # 保持官方Qt DLL原字节；本包qt.conf将插件等路径限定到部署目录。
    command = [str(qt / 'bin/windeployqt.exe'), '--release', '--compiler-runtime', '--no-translations',
               '--no-patchqt', '--no-opengl-sw', '--no-system-d3d-compiler', '--no-system-dxc-compiler', str(executable)]
    with (output / 'windeployqt.log').open('xb') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    (stage / 'qt.conf').write_text('[Paths]\nPrefix=.\nPlugins=.\n', encoding='utf-8')
    shutil.copyfile(ROOT / 'LICENSE', stage / 'LICENSE.txt')
    shutil.copyfile(ROOT / 'docs/releases/v0.11.0-alpha.md', stage / 'README.md')
    (stage / 'examples').mkdir()
    shutil.copyfile(ROOT / 'examples/preview.pcb', stage / 'examples/preview.pcb')
    licenses = stage / 'licenses'
    counts = {}
    for module in QT_SOURCE_HASHES:
        counts[module] = copy_licenses(sources / f'{module}-everywhere-src-{QT_VERSION}.tar.xz', licenses / module)
        shutil.copyfile(qt / f'sbom/{module}-{QT_VERSION}.spdx.json', licenses / f'{module}-{QT_VERSION}.spdx.json')
        for suffix in ('summary', 'opt'):
            configuration = qt / f'config_{module}.{suffix}'
            if configuration.is_file():
                shutil.copyfile(configuration, licenses / module / ('config.' + suffix))
    notices = f'''# 第三方许可与对应源码

PT Renew {VERSION} 使用MIT许可证，见LICENSE.txt。此Windows包动态链接Qt {QT_VERSION}。

## Qt与第三方代码

Qt Core、Gui、Widgets、Concurrent及部署插件来自Qt {QT_VERSION}官方MSVC x64开源预编译包，SVG插件依赖Qt SVG。
本包按GNU LGPL第3版所允许的动态链接方式使用相应Qt库；许可证原文、版权与Qt第三方许可保存在licenses/qtbase与licenses/qtsvg，官方SPDX组件清单一并附上。Qt商业许可不是本项目采用的许可。
用户可以替换兼容的Qt动态链接库。为修改、调试这些库而进行的必要逆向不受本项目额外限制。

本发行页面同时提供以下完整、未修改的对应源码归档，其SHA-256已与Qt官方校验文件比对：
'''
    for module, expected in QT_SOURCE_HASHES.items():
        name = f'{module}-everywhere-src-{QT_VERSION}.tar.xz'
        notices += f'\n- {name}：`{expected}`\n  官方来源：https://download.qt.io/official_releases/qt/6.12/{QT_VERSION}/submodules/{name}\n'
    notices += '''
Qt重建可使用对应源码内README/CMake构建说明及config.summary；需要MSVC x64、CMake和Ninja，使用共享库构建，再替换本包相应DLL。本包保留官方Qt DLL字节，qt.conf仅指定部署目录，不包含Qt源码补丁。
PT Renew对应源码可在https://github.com/Kylineyes/pt_renew/releases/tag/v0.11.0-alpha下载；按README及docs/qt-development.md使用Qt 6.12与MSVC重建，CMake默认动态链接Qt。

## Microsoft运行库

windeployqt收集的vc_redist.x64.exe是Microsoft Visual C++运行库安装器，遵循Microsoft自身许可，运行安装器可查看适用条款。若启动提示缺少VCRUNTIME140或MSVCP140，请先运行该安装器；本包不会自动提升权限或安装运行库。Windows系统组件不属于本项目MIT许可。

## 分发范围

本包不包含原Protel/AUTOTRAX程序、安装盘、原库、用户板图或字体。examples/preview.pcb是本项目合成图形示例。
'''
    (stage / 'THIRD_PARTY_NOTICES.md').write_text(notices, encoding='utf-8')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    metadata = dict(version=VERSION, architecture='windows-x64', source_commit=source_commit, qt_version=QT_VERSION,
                    readonly=True, editing=False, saving=False, clean_windows_verified=False,
                    qt_source_sha256=QT_SOURCE_HASHES, executable_sha256=sha256(executable), license_files=counts)
    (stage / 'release-info.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    files = {p.relative_to(stage).as_posix(): sha256(p) for p in sorted(stage.rglob('*')) if p.is_file()}
    (stage / 'FILES.sha256').write_text(''.join(f'{digest}  {name}\n' for name, digest in files.items()), encoding='utf-8')
    archive = output / (stage.name + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for path in sorted(stage.rglob('*')):
            if path.is_file(): zipped.write(path, stage.name + '/' + path.relative_to(stage).as_posix())
    # Qt对应源码单独作为发行附件，不把SDK或源归档提交进仓库。
    assets = [archive]
    for module in QT_SOURCE_HASHES:
        source = sources / f'{module}-everywhere-src-{QT_VERSION}.tar.xz'
        destination = output / source.name
        shutil.copyfile(source, destination)
        assets.append(destination)
    (output / 'SHA256SUMS.txt').write_text(''.join(f'{sha256(path)}  {path.name}\n' for path in assets), encoding='utf-8')
    result = dict(metadata, package=str(stage), zip=str(archive), zip_sha256=sha256(archive), package_files=len(files) + 1,
                  assets=[str(path) for path in assets] + [str(output / 'SHA256SUMS.txt')])
    (output / 'package-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成独立Windows预发布包，不启动程序或发布到远端')
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--qt', required=True, type=Path)
    parser.add_argument('--qt-sources', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.build, args.output, args.qt, args.qt_sources), ensure_ascii=False, indent=2))
