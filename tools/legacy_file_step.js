/* 单次当前图审核、唯一packet和新图读回；由模型在下一调用中决定下一动作。 */
function createLegacyFileStep(io) {
    const tools = io.tools;
    const canonical = value => JSON.stringify(value, (_, item) => {
        if (item && !Array.isArray(item) && typeof item === 'object') {
            return Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]]));
        }
        return item;
    });
    const equal = (a, b) => canonical(a) === canonical(b);
    const quote = value => "'" + String(value).replace(/'/g, "''") + "'";
    const normalize = value => String(value).replace(/\\/g, '/').replace(/\/$/, '').toLowerCase();
    async function optional(path) {
        try { return JSON.parse(await tools.read({path, offset: 1, limit: 2000})); }
        catch (error) { if (/ENOENT|no such file/i.test(String(error))) return null; throw error; }
    }
    return async function sendAndRead(options) {
        let stage = '参数';
        let packetWritten = false;
        try {
            const {slot, waitScript, state, request, observations} = options;
            if (!slot || /(^|[\\/])\.\.([\\/]|$)/.test(slot) || !/^[A-Za-z]:[\\/]/.test(slot)) {
                throw new Error('必须使用本工作树新槽绝对路径');
            }
            if (!/^[A-Za-z]:[\\/]/.test(waitScript || '') || /(^|[\\/])\.{1,2}([\\/]|$)/.test(waitScript) ||
                !normalize(waitScript).endsWith('/tools/wait-legacyfilestep.ps1')) {
                throw new Error('必须显式指定同树tools内已审阅冻结等待脚本');
            }
            const repository = normalize(waitScript).slice(0, -'/tools/wait-legacyfilestep.ps1'.length);
            if (/(^|[\\/])\.([\\/]|$)/.test(slot) || !normalize(slot).startsWith(repository + '/.local-analysis/')) {
                throw new Error('新槽不属于等待脚本所在工作树忽略目录');
            }
            if (!/^step-[0-9]{3}-[a-z0-9-]+$/.test(state.step) || !/^[a-f0-9]{32}$/.test(state.nonce)) {
                throw new Error('当前步骤或nonce无效');
            }
            if (!/^[a-z0-9-]+$/.test(request.name) || !['Launch', 'App', 'Click', 'Shortcut'].includes(request.tool)) {
                throw new Error('本合一调用只接受一个显式业务动作，生命周期沿原流程');
            }
            for (const key of ['task', 'dispatch', 'session']) {
                if (typeof state[key] !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(state[key])) throw new Error('身份字段无效');
            }
            const timeoutMs = options.timeoutMs === undefined ? 10000 : options.timeoutMs;
            if (!Number.isInteger(timeoutMs) || timeoutMs < 100 || timeoutMs > 15000) throw new Error('等待上限必须为100至15000毫秒');
            const root = slot.replace(/[\\/]$/, '') + '/';
            const base = root + 'submit-queue/packet-' + request.name;
            const binding = {task: state.task, dispatch: state.dispatch, session: state.session};
            stage = '计划与冻结来源';
            const plan = await optional(root + 'live-plan.json');
            if (!plan || normalize(plan.slot) !== normalize(slot) ||
                !Object.keys(binding).every(key => plan[key] === binding[key])) {
                throw new Error('新槽计划路径或Task/Dispatch/会话身份不符');
            }
            if (!Array.isArray(plan.frozen_files)) throw new Error('计划缺少冻结来源');
            for (const source of [normalize(waitScript), repository + '/tools/legacy_file_step.js']) {
                const entries = plan.frozen_files.filter(item => normalize(item.path) === source);
                if (entries.length !== 1 || !Number.isInteger(entries[0].bytes) || entries[0].bytes <= 0 ||
                    !/^[a-f0-9]{64}$/.test(entries[0].sha256)) {
                    throw new Error('等待脚本或合一适配器未在同树计划中唯一冻结');
                }
            }
            const packet = {...binding, previous: state.step, nonce: state.nonce, request};
            const prefix = 'step-' + String(Number(state.step.slice(5, 8)) + 1).padStart(3, '0') + '-' + request.name;
            stage = '同名包检查';
            const old = [];
            for (const suffix of ['.json', '.submitted', '.rejected']) {
                const value = await optional(base + suffix);
                if (value !== null) old.push({suffix, value});
            }
            const oldResult = await optional(base + '.result');
            if (old.length > 1) throw new Error('同名包存在多个版本，不能重发');
            if (old.length === 1) {
                if (!equal(old[0].value, packet)) throw new Error('同名旧包内容不符，不能覆盖或重发');
                if (old[0].suffix === '.rejected') return {status: 'refused', stage, reason: '原包已拒绝，只能停止业务', packetWritten};
                // 已提交或仍在队列时只续等，既不重写审核也不再次写packet。
            } else {
                if (oldResult !== null || await optional(root + prefix + '-complete.json') !== null) {
                    throw new Error('已有同名结果或完成证据但缺原包，不能重新创建');
                }
                stage = '当前实际观察审核';
                const current = await optional(root + 'current-state.json');
                const frozen = await optional(root + state.step + '-observation.json');
                if (!equal(current, state) || !equal(frozen, state)) throw new Error('调用不是当前原观测或nonce已变化');
                for (const kind of ['host', 'guest']) {
                    if (!Array.isArray(state[kind])) throw new Error('原图清单缺失');
                    if (state[kind].length && (!observations || typeof observations[kind] !== 'string' || !observations[kind].trim())) {
                        throw new Error('必须提供模型已经实际看图的当前观察，不自动判图');
                    }
                }
                for (const kind of ['host', 'guest']) {
                    if (!state[kind].length) continue;
                    await tools.write({path: root + state.step + '-' + kind + '-read-review.json', content: JSON.stringify({
                        ...binding, step: state.step, nonce: state.nonce, model: 'deng/gpt-6.1-sol', thinking: 'high',
                        images: state[kind], observation: observations[kind]
                    })});
                }
                stage = '唯一投递';
                await tools.write({path: base + '.json', content: JSON.stringify(packet)});
                packetWritten = true;
            }
            stage = '有界纯文件等待';
            const command = '& ' + quote(waitScript) + ' -Slot ' + quote(slot) +
                ' -Task ' + quote(state.task) + ' -Dispatch ' + quote(state.dispatch) +
                ' -Session ' + quote(state.session) + ' -Previous ' + quote(state.step) +
                ' -Nonce ' + quote(state.nonce) + ' -Name ' + quote(request.name) + ' -TimeoutMs ' + timeoutMs;
            const execution = await tools.powershell({command, timeout: 20});
            const wait = JSON.parse(execution.output.replace(/^\uFEFF/, '').trim());
            if (!['ready', 'pending', 'refused', 'error'].includes(wait.status)) throw new Error('等待结果状态无效');
            if (wait.status !== 'ready') return {...wait, packetWritten, shellExitCode: execution.exit_code};
            if (execution.exit_code !== 0 || execution.truncated) throw new Error('等待工具退出异常或输出截断');
            stage = '精确新图';
            const current = await optional(root + 'current-state.json');
            if (!equal(current, wait.state) || current.step !== prefix + '-post' || current.nonce === state.nonce) {
                throw new Error('等待后状态再次变化或不是预期新动作');
            }
            const receipt = await optional(base + '.result');
            if (!receipt || receipt.submitted !== true || receipt.packet !== 'packet-' + request.name + '.json') {
                throw new Error('新图读回前原包结果不符');
            }
            const native = await optional(root + current.step + '-native-after.json');
            if (!native || !Array.isArray(native.visible_windows)) throw new Error('新图缺原native后验');
            const nativeSummary = {observed_at: native.observed_at, windows: native.visible_windows.filter(window =>
                Number.isInteger(options.targetPid) && window.process && window.process.pid === options.targetPid).map(window => ({
                hwnd: window.hwnd, title: window.title, rect: window.rect, pid: window.process && window.process.pid
            }))};
            const blocks = [];
            for (const kind of ['host', 'guest']) {
                if (!Array.isArray(current[kind]) || (kind === 'host' && !current[kind].length)) throw new Error('新原图清单无效');
                for (const item of current[kind]) {
                    if (/(^|[\\/])\.\.([\\/]|$)/.test(item.path) || !normalize(item.path).startsWith(normalize(slot) + '/')) throw new Error('新原图路径越过本槽');
                    if (kind === 'host' && !normalize(item.path).includes('/' + current.step + '-')) throw new Error('host不是新动作原图');
                    const block = await tools.read({path: item.path, offset: 1, limit: 10});
                    if (block.type !== 'image' || block.mimeType !== 'image/png' || !block.data) throw new Error('新原图读取未返回PNG');
                    blocks.push(block);
                }
            }
            io.text({status: 'observed', state: current, native: nativeSummary, packetWritten, wait_ms: wait.elapsed_ms});
            for (const block of blocks) io.image(block);
            // 新图只在此返回；这里不生成新图审核，不选择菜单，也不发下一包。
            return {status: 'observed', state: current, native: nativeSummary, packetWritten, wait_ms: wait.elapsed_ms};
        } catch (error) {
            return {status: 'error', stage, reason: String(error), packetWritten};
        }
    };
}
