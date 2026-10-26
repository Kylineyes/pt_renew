#include "experiment/AsyncExperiment.h"
#include <QCoreApplication>
#include <QDateTime>
#include <QDir>
#include <QElapsedTimer>
#include <QFile>
#include <QJsonDocument>
#include <QMutex>
#include <QMutexLocker>
#include <QSaveFile>
#include <QThread>
#include <QUuid>
#include <QtCore/qt_windows.h>
#include <algorithm>

namespace pt::experiment {
struct Request {
    QString id, kind;
    bool gated = false;
    bool aborted = false;
    HANDLE release = nullptr, cancel = nullptr;
    ~Request() {
        if (release) CloseHandle(release);
        if (cancel) CloseHandle(cancel);
    }
};
namespace {
struct Runtime {
    QMutex mutex;
    QFile trace;
    QElapsedTimer clock;
    Config config;
    QString run;
    quint64 sequence = 0, requests = 0;
    int remainingSkip = 0;
    bool armed = true, healthy = true;
    HANDLE owner = nullptr;
    ~Runtime() { if (owner) CloseHandle(owner); }
};
std::shared_ptr<Runtime> runtime;
thread_local RequestPtr current;

QString creationTime(HANDLE process) {
    FILETIME created{}, exited{}, kernel{}, user{};
    if (!GetProcessTimes(process, &created, &exited, &kernel, &user)) return {};
    return QString::number((quint64(created.dwHighDateTime) << 32) | created.dwLowDateTime);
}
// 调用方持锁；序号、时间戳和落盘顺序属于同一个进程时钟域。
bool record(Runtime& state, const RequestPtr& request, const QString& event, QJsonObject fields = {}) {
    fields.insert(QStringLiteral("event"), event);
    fields.insert(QStringLiteral("run_id"), state.run);
    fields.insert(QStringLiteral("request_id"), request ? request->id : QString());
    fields.insert(QStringLiteral("kind"), request ? request->kind : QString());
    fields.insert(QStringLiteral("sequence"), QString::number(++state.sequence));
    fields.insert(QStringLiteral("monotonic_ns"), QString::number(state.clock.nsecsElapsed()));
    fields.insert(QStringLiteral("wall_ms"), QString::number(QDateTime::currentMSecsSinceEpoch()));
    fields.insert(QStringLiteral("pid"), QString::number(QCoreApplication::applicationPid()));
    fields.insert(QStringLiteral("thread_id"), QString::number(quintptr(QThread::currentThreadId())));
    const auto bytes = QJsonDocument(fields).toJson(QJsonDocument::Compact) + '\n';
    if (state.trace.write(bytes) != bytes.size() || !state.trace.flush()) state.healthy = false;
    return state.healthy;
}
void event(const RequestPtr& request, const QString& name, const QJsonObject& fields = {}) {
    const auto state = runtime;
    if (!state || !request) return;
    QMutexLocker lock(&state->mutex);
    record(*state, request, name, fields);
}
}

bool configure(const Config& config, QString* error) {
    const auto fail = [error](const QString& text) { if (error) *error = text; return false; };
    if (runtime) return fail(QStringLiteral("实验运行已配置，禁止重置时间线或重复布置门闩。"));
    if (!QCoreApplication::instance() || !QThread::isMainThread())
        return fail(QStringLiteral("必须在应用主线程配置实验。"));
    if ((config.kind != QStringLiteral("net") && config.kind != QStringLiteral("copper")) ||
        config.ownerPid <= 0 || config.ownerPid > MAXDWORD || config.skip < 0 ||
        config.watchdogMilliseconds < 1 || config.watchdogMilliseconds > 60000)
        return fail(QStringLiteral("实验类型、持有者PID、跳过数或看门狗参数无效。"));
    if (config.directory.isEmpty() || !QDir::isAbsolutePath(config.directory))
        return fail(QStringLiteral("实验目录必须为新的绝对路径。"));
    const QDir directory(config.directory);
    if (directory.exists() && !directory.entryList(QDir::AllEntries | QDir::NoDotAndDotDot | QDir::Hidden | QDir::System).isEmpty())
        return fail(QStringLiteral("实验目录非空，禁止覆盖旧证据。"));
    auto state = std::make_shared<Runtime>();
    state->owner = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, DWORD(config.ownerPid));
    if (!state->owner || WaitForSingleObject(state->owner, 0) != WAIT_TIMEOUT)
        return fail(QStringLiteral("无法绑定仍在运行的实验持有者。"));
    if (!directory.mkpath(QStringLiteral("."))) return fail(QStringLiteral("无法创建实验目录。"));
    state->trace.setFileName(directory.filePath(QStringLiteral("events.jsonl")));
    if (!state->trace.open(QIODevice::WriteOnly | QIODevice::NewOnly))
        return fail(QStringLiteral("无法独占创建实验事件记录。"));
    state->config = config;
    state->remainingSkip = config.skip;
    state->run = QUuid::createUuid().toString(QUuid::WithoutBraces);
    state->clock.start();
    if (!record(*state, {}, QStringLiteral("run-started"), {
        {QStringLiteral("candidate_type"), QStringLiteral("独立异步实验构建，不代表固定候选通过")},
        {QStringLiteral("owner_pid"), QString::number(config.ownerPid)},
        {QStringLiteral("owner_creation_filetime"), creationTime(state->owner)},
        {QStringLiteral("kind_configured"), config.kind},
        {QStringLiteral("skip"), config.skip},
        {QStringLiteral("watchdog_ms"), config.watchdogMilliseconds}}))
        return fail(QStringLiteral("无法持久化实验启动记录。"));
    runtime = std::move(state);
    return true;
}

void shutdown() {
    const auto state = runtime;
    if (!state) return;
    QMutexLocker lock(&state->mutex);
    record(*state, {}, QStringLiteral("run-stopped"));
    runtime.reset();
}

RequestPtr begin(const QString& kind, const QJsonObject& fields) {
    const auto state = runtime;
    if (!state) return {};
    QMutexLocker lock(&state->mutex);
    auto request = std::make_shared<Request>();
    request->id = QString::number(++state->requests);
    request->kind = kind;
    if (state->armed && kind == state->config.kind) {
        if (state->remainingSkip > 0) --state->remainingSkip;
        else { request->gated = true; state->armed = false; }
    }
    auto metadata = fields;
    metadata.insert(QStringLiteral("gated"), request->gated);
    record(*state, request, QStringLiteral("request-created"), metadata);
    if (!request->gated) return request;
    const auto prefix = QStringLiteral("Local\\PtRenewAsync-%1-%2-").arg(state->run, request->id);
    const auto releaseName = prefix + QStringLiteral("release");
    const auto cancelName = prefix + QStringLiteral("cancel");
    request->release = CreateEventW(nullptr, TRUE, FALSE, reinterpret_cast<LPCWSTR>(releaseName.utf16()));
    const bool releaseNew = request->release && GetLastError() != ERROR_ALREADY_EXISTS;
    request->cancel = CreateEventW(nullptr, TRUE, FALSE, reinterpret_cast<LPCWSTR>(cancelName.utf16()));
    const bool cancelNew = request->cancel && GetLastError() != ERROR_ALREADY_EXISTS;
    QJsonObject manifest{{QStringLiteral("run_id"), state->run}, {QStringLiteral("request_id"), request->id},
        {QStringLiteral("kind"), kind}, {QStringLiteral("pid"), QString::number(QCoreApplication::applicationPid())},
        {QStringLiteral("creation_filetime"), creationTime(GetCurrentProcess())},
        {QStringLiteral("release_event"), releaseName}, {QStringLiteral("cancel_event"), cancelName}};
    QSaveFile file(QDir(state->config.directory).filePath(QStringLiteral("request-%1.json").arg(request->id)));
    const auto bytes = QJsonDocument(manifest).toJson();
    const bool saved = file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size() && file.commit();
    if (!releaseNew || !cancelNew || !saved || !state->healthy) {
        request->aborted = true;
        record(*state, request, QStringLiteral("aborted"), {{QStringLiteral("reason"), QStringLiteral("门闩或证据初始化失败")}});
    }
    return request;
}

Scope::Scope(RequestPtr request) : m_previous(std::move(current)) { current = std::move(request); }
Scope::~Scope() { current = std::move(m_previous); }

void checkpoint(const QString& stage) {
    const auto state = runtime;
    const auto request = current;
    if (!state || !request) return;
    event(request, QStringLiteral("worker-entered"), {{QStringLiteral("stage"), stage}});
    if (!request->gated || request->aborted) return;
    if (QThread::isMainThread()) {
        request->aborted = true;
        event(request, QStringLiteral("aborted"), {{QStringLiteral("reason"), QStringLiteral("禁止阻塞GUI线程")}});
        return;
    }
    {
        QMutexLocker lock(&state->mutex);
        if (!record(*state, request, QStringLiteral("gate-ready"))) {
            request->aborted = true;
            return;
        }
    }
    const HANDLE handles[]{request->cancel, state->owner, request->release};
    QElapsedTimer watchdog; watchdog.start();
    DWORD status = WAIT_TIMEOUT;
    while (watchdog.elapsed() < state->config.watchdogMilliseconds) {
        const auto remaining = state->config.watchdogMilliseconds - watchdog.elapsed();
        status = WaitForMultipleObjects(3, handles, FALSE, DWORD(std::min<qint64>(remaining, 1000)));
        if (status != WAIT_TIMEOUT) break;
    }
    // cancel和持有者退出优先；即使release同时置位，也不能把失去持有者记为正常释放。
    if (status == WAIT_OBJECT_0 + 2 && WaitForSingleObject(state->owner, 0) == WAIT_TIMEOUT &&
        WaitForSingleObject(request->cancel, 0) == WAIT_TIMEOUT) {
        event(request, QStringLiteral("gate-released"));
    } else {
        request->aborted = true;
        const auto reason = status == WAIT_TIMEOUT ? QStringLiteral("看门狗超时") :
            status == WAIT_OBJECT_0 + 1 ? QStringLiteral("持有者退出") :
            status == WAIT_OBJECT_0 ? QStringLiteral("控制端取消") : QStringLiteral("等待门闩失败或持有者已失效");
        event(request, QStringLiteral("aborted"), {{QStringLiteral("reason"), reason}});
    }
}

void returned(const QJsonObject& fields) { event(current, QStringLiteral("worker-returned"), fields); }
void callback(const RequestPtr& request, bool accepted, const QJsonObject& fields) {
    auto metadata = fields;
    metadata.insert(QStringLiteral("accepted"), accepted);
    metadata.insert(QStringLiteral("experiment_aborted"), request ? request->aborted : false);
    event(request, accepted ? QStringLiteral("callback-accepted") : QStringLiteral("callback-discarded"), metadata);
}
void documentPublished(const QJsonObject& fields) {
    const auto state = runtime;
    if (!state) return;
    QMutexLocker lock(&state->mutex);
    record(*state, {}, QStringLiteral("document-published"), fields);
}
}
