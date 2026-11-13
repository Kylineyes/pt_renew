/* 无GUI合成IO验证：只观察文件写入和单次等待，不加载桌面或真实图。 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const crypto = require('node:crypto');
const source = fs.readFileSync(path.join(__dirname, '../tools/legacy_file_step.js'), 'utf8');
const create = vm.runInNewContext(source + '\ncreateLegacyFileStep;');
const clone = value => JSON.parse(JSON.stringify(value));
function fixture() {
    const slot = 'C:/repo/.local-analysis/fixture/slot';
    const state = {task:'task_fixture',dispatch:'ctx_fixture',session:'fixture-session',step:'step-005-old-post',nonce:'1'.repeat(32),
        host:[{path:slot+'/step-005-old-post-00.png',sha256:'a'}],guest:[{path:slot+'/captures/pt_000.png',sha256:'b'}]};
    const current = {...clone(state),step:'step-006-one-key-post',nonce:'2'.repeat(32),
        host:[{path:slot+'/step-006-one-key-post-00.png',sha256:'c'}],guest:[]};
    const request = {name:'one-key',tool:'Shortcut',purpose:'navigate_down',arguments:{shortcut:'down'}};
    const files = new Map();
    files.set(slot+'/live-plan.json',{...clone(state),slot,frozen_files:[
        {path:'C:/repo/tools/legacy_file_step.js',bytes:Buffer.byteLength(source),sha256:crypto.createHash('sha256').update(source).digest('hex')},
        {path:'C:/repo/tools/Wait-LegacyFileStep.ps1',bytes:fs.statSync(path.join(__dirname,'../tools/Wait-LegacyFileStep.ps1')).size,
            sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'../tools/Wait-LegacyFileStep.ps1'))).digest('hex')}
    ]});
    const writes = [], images = [], texts = [], waits = [];
    files.set(slot+'/current-state.json', clone(state));
    files.set(slot+'/'+state.step+'-observation.json', clone(state));
    let waitStatus = 'ready';
    let readyState = current;
    let exitCode = 0;
    const tools = {
        async read({path}) {
            if (path.endsWith('.png')) return {type:'image',mimeType:'image/png',data:'合成块，不作为真实图输出'};
            if (!files.has(path)) throw new Error('ENOENT: '+path);
            return JSON.stringify(files.get(path));
        },
        async write({path,content}) { writes.push(path); files.set(path,JSON.parse(content)); return '已写'; },
        async powershell(args) {
            waits.push(args);
            const queue = slot+'/submit-queue/packet-one-key';
            if (files.has(queue+'.json')) { files.set(queue+'.submitted',files.get(queue+'.json'));files.delete(queue+'.json'); }
            if (waitStatus === 'ready') {
                files.set(slot+'/current-state.json',clone(readyState));
                files.set(queue+'.result',{packet:'packet-one-key.json',submitted:true});
                files.set(slot+'/'+readyState.step+'-native-after.json',{observed_at:'合成时刻',visible_windows:[
                    {hwnd:9,title:'合成目标',rect:[0,0,10,10],process:{pid:7}},
                    {hwnd:8,title:'其它目标',rect:[0,0,10,10],process:{pid:8}}]});
            }
            return {output:JSON.stringify({status:waitStatus,state:readyState,elapsed_ms:500}),exit_code:exitCode,truncated:false};
        }
    };
    const run=create({tools,image:block=>images.push(block),text:item=>texts.push(item)});
    const options={slot,waitScript:'C:/repo/tools/Wait-LegacyFileStep.ps1',state,request,
        observations:{host:'模型已看合成host',guest:'模型已看合成guest'},targetPid:7};
    return {slot,state,current,request,files,writes,images,texts,waits,run,options,
        status:value=>{waitStatus=value;},ready:value=>{readyState=value;},exit:value=>{exitCode=value;}};
}
const tests=[];
function test(name,body){tests.push({name,body});}
test('单动作审核投递等待及新host实际读回',async()=>{
    const f=fixture(),r=await f.run(f.options);
    assert.equal(r.status,'observed');assert.equal(f.images.length,1);assert.equal(f.waits.length,1);
    assert.equal(f.writes.filter(p=>p.includes('/submit-queue/')).length,1);
    assert.equal(f.writes.length,3);assert.equal(r.native.windows.length,1);assert.equal(r.native.windows[0].pid,7);
    assert.equal(f.waits[0].timeout,20);assert.match(f.waits[0].command,/-TimeoutMs 10000$/);
    assert(!f.writes.some(p=>p.includes('step-006-')),'新图尚未由模型看，不得自动生成审核或下一包');
});
test('pending不读图，续等已归档同包不重写审核或重发',async()=>{
    const f=fixture();f.status('pending');
    assert.equal((await f.run(f.options)).status,'pending');assert.equal(f.images.length,0);
    const count=f.writes.length;f.status('ready');
    assert.equal((await f.run(f.options)).status,'observed');assert.equal(f.writes.length,count);assert.equal(f.waits.length,2);
});
test('原包拒绝停止而不读图',async()=>{
    const f=fixture();f.status('refused');f.exit(3);
    const r=await f.run(f.options);assert.equal(r.status,'refused');assert.equal(r.shellExitCode,3);assert.equal(f.images.length,0);
});
test('同名旧包不同内容零写入零等待',async()=>{
    const f=fixture();f.files.set(f.slot+'/submit-queue/packet-one-key.submitted',{task:'其它任务'});
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);assert.equal(f.waits.length,0);
});
test('当前状态过期零写入',async()=>{
    const f=fixture();f.files.set(f.slot+'/current-state.json',f.current);
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);
});
test('当前任务身份错误零写入',async()=>{
    const f=fixture();f.options.state={...f.state,task:'task_other'};
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);
});
test('缺少客体实际观察不能部分写审核',async()=>{
    const f=fixture();delete f.options.observations.guest;
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);
});
test('等待声称ready但旧nonce不输出图片',async()=>{
    const f=fixture();f.ready(f.state);
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.images.length,0);
});
test('等待工具异常退出不读新图',async()=>{
    const f=fixture();f.exit(2);
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.images.length,0);
});
test('等待超过上限零写入',async()=>{
    const f=fixture();f.options.timeoutMs=15001;
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);
});
test('树外新槽零写入零等待',async()=>{
    const f=fixture();f.options.slot='C:/outside/slot';
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);assert.equal(f.waits.length,0);
});
test('计划身份不符零写入零等待',async()=>{
    const f=fixture();f.files.get(f.slot+'/live-plan.json').task='task_other';
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);assert.equal(f.waits.length,0);
});
test('等待脚本未冻结零写入零等待',async()=>{
    const f=fixture();f.files.get(f.slot+'/live-plan.json').frozen_files.pop();
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);assert.equal(f.waits.length,0);
});
test('错树等待脚本零写入零等待',async()=>{
    const f=fixture();f.options.waitScript='C:/other/tools/Wait-LegacyFileStep.ps1';
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,0);assert.equal(f.waits.length,0);
});
test('已投递同包续等仍先核计划与冻结归属',async()=>{
    const f=fixture();f.status('pending');assert.equal((await f.run(f.options)).status,'pending');
    const count=f.writes.length;f.files.get(f.slot+'/live-plan.json').frozen_files=[];
    assert.equal((await f.run(f.options)).status,'error');assert.equal(f.writes.length,count);assert.equal(f.waits.length,1);
});
(async()=>{
    for(const t of tests){await t.body();console.log('通过：'+t.name);}
    console.log(JSON.stringify({passed:tests.length,failed:0,scope:'合成IO，不是真实桌面/菜单验收'}));
})().catch(error=>{console.error(error);process.exitCode=1;});
