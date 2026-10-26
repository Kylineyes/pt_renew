#pragma once
#include <QJsonObject>
#include <QString>
#include <memory>

namespace pt::experiment {
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
struct Request;
using RequestPtr = std::shared_ptr<Request>;
struct Config {
    QString directory;
    QString kind;
    qint64 ownerPid = 0;
    int skip = 0;
    int watchdogMilliseconds = 60000;
};
// 仅实验构建存在；一次进程只允许配置一个独立证据目录和一种单次门闩。
bool configure(const Config& config, QString* error);
void shutdown();
RequestPtr begin(const QString& kind, const QJsonObject& fields);
class Scope final {
public:
    explicit Scope(RequestPtr request);
    ~Scope();
    Scope(const Scope&) = delete;
    Scope& operator=(const Scope&) = delete;
private:
    RequestPtr m_previous;
};
void checkpoint(const QString& stage);
void returned(const QJsonObject& fields);
void callback(const RequestPtr& request, bool accepted, const QJsonObject& fields);
void documentPublished(const QJsonObject& fields);
#else
struct Request {};
using RequestPtr = std::shared_ptr<Request>;
inline RequestPtr begin(const QString&, const QJsonObject&) { return {}; }
class Scope final {
public:
    explicit Scope(const RequestPtr&) {}
};
inline void checkpoint(const QString&) {}
inline void returned(const QJsonObject&) {}
inline void callback(const RequestPtr&, bool, const QJsonObject&) {}
inline void documentPublished(const QJsonObject&) {}
#endif
}
