"""离线冻结产品客户端、见证器、部署和输入；无启动/控制入口，不生成批准。"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import shutil

from async_product_client.core import digest, require
from async_product_client.product import tree_hashes

FROZEN_EXPERIMENT_SHA = '782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac'
WITNESS_FILES = ('control_process_supervisor.py', 'control_witness_launch.py', 'control_supervisor_runner.py')
SERVICE_FILES = ('run_control_diagnostics.py', 'control_diagnostics.py', 'control_indicator_health.py',
                 'control_bitmap_surface.py', 'control_bitmap_surface_model.py', 'control_surface_approval.py',
                 'control_app_refresh.py', 'control_target_activation.py', 'control_test_window.py',
                 'control_bitmap_timing.py')


def freeze(destination, *, references, inputs):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    require({'experiment', 'fixed', 'stable', 'control_package'} <= references.keys(), '冻结外部依赖不完整')
    for label, reference in references.items():
        require(tree_hashes(reference['root'], ignore_bytecode=True) == reference['files'],
                '只读参考摘要不符：' + label)
    require(len(references['experiment']['files']) == 22
            and references['experiment']['files'].get('pt-renew.exe') == FROZEN_EXPERIMENT_SHA,
            '冻结实验22文件/EXE与接手基线不符')
    require(len(references['fixed']['files']) == 23 and len(references['stable']['files']) == 22
            and len(references['control_package']['files']) == 77, '固定/稳定/控制包文件集合不符')
    require(len(inputs) == 3 and {Path(p).name for p in inputs} == {'board.pcb', 'a.net', 'b.net'},
            '必须冻结本轮三份输入副本')
    for path, sha in inputs.items():
        require(digest(Path(path).read_bytes()) == sha, '输入副本摘要改变')
    candidate = destination / 'candidate'
    candidate.mkdir()
    source = Path(__file__).resolve().parents[1]
    names = [p.relative_to(source) for p in (source / 'tools/async_product_client').glob('*.py')]
    names += [Path('tools') / name for name in WITNESS_FILES + SERVICE_FILES]
    names += [Path(name) for name in ('tools/freeze_async_product.py', 'tools/probe_async_images.py',
                                     'tools/control_geometry.py', 'tools/audit_async_race.py',
                                     'tests/test_async_product_client.py', 'tests/test_async_product_adapters.py',
                                     'tests/test_async_product_gate.py', 'tests/test_async_product_native.py',
                                     'tests/test_async_product_probe.py', 'tests/test_async_product_file_dialog.py',
                                     'tests/test_async_product_session.py', 'tests/test_async_product_witness.py',
                                     'tests/test_async_product_batch.py', 'tests/test_async_product_deadlines.py',
                                     'tests/test_async_product_runtime.py', 'tests/test_async_product_connection.py',
                                     'tests/test_async_product_shutdown.py', 'tests/fixtures/async_product_runtime_driver.py',
                                     'tests/test_audit_async_race.py',
                                     'tests/test_probe_async_images.py', 'tests/test_freeze_async_product.py',
                                     'docs/async-product-deadlines.md',
                                     'docs/async-product-batch-observation.md', 'docs/async-product-session.md', 'docs/async-product-file-dialog.md', 'docs/async-product-bounded-probe.md', 'docs/async-product-gate-binding.md',
                                     'docs/async-product-evidence-adapters.md', 'docs/async-product-client-offline.md',
                                     'docs/async-product-client-contract.md')]
    for name in names:
        path = candidate / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, path)
        if name.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'))
    for label, folder in (('experiment', 'deployment'), ('control_package', 'runtime/windows_mcp')):
        reference = references[label]
        for name, sha in reference['files'].items():
            path = candidate / folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(reference['root']) / name, path)
            require(digest(path.read_bytes()) == sha, '复制时外部依赖改变')
    package_manifest = dict(source=references['control_package']['root'], package=str(candidate / 'runtime/windows_mcp'),
                            files=references['control_package']['files'], installed_writes=0)
    with (candidate / 'runtime/package-manifest.json').open('x', encoding='utf-8') as out:
        json.dump(package_manifest, out, ensure_ascii=False, indent=2)
    for path, sha in inputs.items():
        target = candidate / 'inputs' / Path(path).name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
        require(digest(target.read_bytes()) == sha, '复制时输入改变')
    # 冻结前后复核来源，避免把不同时点的文件拼成一次候选。
    for label, reference in references.items():
        require(tree_hashes(reference['root'], ignore_bytecode=True) == reference['files'],
                '冻结期间只读参考改变：' + label)
    from async_product_client.budget import session_budget
    plan = dict(schema_version=1, purpose='offline-product-client', ready_for_live=False,
                permission_confirmed=False, task_id=None, dispatch_id=None, run_id=None, session_id=None,
                max_product_launches=0, live_adapter_frozen=False, model_timing_verified=False,
                mcp_result_adapter_offline_tested=True, original_popen_adapter_offline_tested=True,
                application_uuid_binding_offline_tested=True, gate_event_adapter_offline_tested=True,
                unique_release_offline_tested=True, native_window_adapter_offline_tested=True,
                native_window_adapter_verified=False, file_dialog_stage_verified=False,
                bounded_probe_offline_tested=True, main_discovery_offline_tested=True,
                bounded_probe_runtime_verified=False, probe_max_queries=32, probe_query_timeout_ms=5000,
                file_dialog_offline_tested=True, original_popen_registry_offline_tested=True,
                process_chain_runtime_verified=False, session_offline_tested=True,
                batch_observation_offline_tested=True, batch_observation_runtime_verified=False,
                creator_relay_offline_tested=True, phase_remaining_deadline_offline_tested=True,
                creator_runtime_no_gui_chain_tested=True, original_service_pipe_offline_tested=True,
                arbitrary_stage_shutdown_offline_tested=True, production_bootstrap_runtime_verified=False,
                passive_original_popen_hold_after_failure=True,
                session_budgets={kind: session_budget(kind) for kind in ('net', 'copper')},
                default_enabled=False, watchdog_ms=60000, t1_read_ack_ms=20000,
                t2_edit_read_ack_ms=50000, t3_release_start_before_ms=55000,
                release_completion_before_ms=60000, local_wait_chunk_ms=1000,
                reject_zero_desktop_ms=120000, close_tool_margin_ms=35000,
                close_original_popen_wait_ms=5000, close_stop_margin_ms=40000,
                diagnostic_budget_seconds=600, total_budget_seconds=900,
                budget_armed=False,
                blockers=['批量观察含发现NET31/铜22次在32次内，但真实冷启动/COM/截图/read总时限仍未验证',
                          '原生文件框/控件/路径输入尚无真实GUI兼容性和时限证据',
                          '阶段剩余时限拒绝已接入，但不能证明同步预检或在途COM会被及时中断',
                          '生产创建者及原服务管道已接入，无GUI四身份链通过；实际控制服务/产品驱动与原退出链仍待验证',
                          '有界探针与主窗发现尚无真实产品UIA/COM兼容性与时限证明',
                          '尚无新Task/Dispatch及具体时间范围的最终审阅材料'])
    with (candidate / 'plan.json').open('x', encoding='utf-8') as out:
        json.dump(plan, out, ensure_ascii=False, indent=2)
    files = tree_hashes(candidate)
    result = dict(schema_version=1, files=files, references=references, inputs=inputs,
                  plan=plan, desktop_requests=0, product_launches=0)
    with (destination / 'frozen-manifest.json').open('x', encoding='utf-8') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='仅生成默认禁用的新产品离线候选，无现场入口')
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--references', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.destination,
                    references=json.loads(args.references.read_text(encoding='utf-8-sig')),
                    inputs=json.loads(args.inputs.read_text(encoding='utf-8-sig')))
    print(json.dumps(dict(files=len(result['files']), ready_for_live=False, desktop_requests=0), ensure_ascii=False))
