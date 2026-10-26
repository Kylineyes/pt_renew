#include "ui/MainWindow.h"
#include "experiment/AsyncExperiment.h"
#include <QTextStream>

#include <QApplication>
#include <QCommandLineParser>
#include <QCommandLineOption>
#include <QTimer>
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
#include <QThreadPool>
#endif

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("pt-renew"));
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
    QCoreApplication::setApplicationVersion(QStringLiteral("0.11.0-async-experiment"));
#else
    QCoreApplication::setApplicationVersion(QStringLiteral("0.11.0"));
#endif
    QCoreApplication::setOrganizationName(QStringLiteral("PtRenew"));
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("AUTOTRAX 重建工程：自由走线内存编辑（不支持保存）、只读库/网表及受限铜层分析（非完整 DRC）。"));
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addOption(QCommandLineOption(QStringLiteral("library"),QStringLiteral("在独立只读窗口打开 LIB，不放置到板图。"),QStringLiteral("路径")));
    parser.addOption(QCommandLineOption(QStringLiteral("netlist"),QStringLiteral("只读载入外部 NET；若指定板图则在板图成功载入后映射。"),QStringLiteral("路径")));
    parser.addPositionalArgument(QStringLiteral("文件"), QStringLiteral("可选：只读载入 PCB FILE 4 原件，建立内存工作副本；不支持保存。"), QStringLiteral("[文件]"));
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
    parser.addOption(QCommandLineOption(QStringLiteral("async-experiment-dir"), QStringLiteral("启用独立实验事件记录，必须使用新的绝对路径目录。"), QStringLiteral("目录")));
    parser.addOption(QCommandLineOption(QStringLiteral("async-experiment-kind"), QStringLiteral("单次后台门闩类型：net或copper。"), QStringLiteral("类型")));
    parser.addOption(QCommandLineOption(QStringLiteral("async-experiment-owner"), QStringLiteral("持有者进程PID；该进程退出则实验中止并释放后台。"), QStringLiteral("PID")));
    parser.addOption(QCommandLineOption(QStringLiteral("async-experiment-skip"), QStringLiteral("先跳过同类型异步请求的次数。"), QStringLiteral("次数"), QStringLiteral("0")));
#endif
    parser.process(app);
    if (parser.positionalArguments().size() > 1) parser.showHelp(2);
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
    const bool configured=parser.isSet(QStringLiteral("async-experiment-dir"));
    const bool hasExtra=parser.isSet(QStringLiteral("async-experiment-kind")) || parser.isSet(QStringLiteral("async-experiment-owner")) || parser.isSet(QStringLiteral("async-experiment-skip"));
    if (configured || hasExtra) {
        bool ownerOk=false, skipOk=false;
        pt::experiment::Config config;
        config.directory=parser.value(QStringLiteral("async-experiment-dir"));
        config.kind=parser.value(QStringLiteral("async-experiment-kind"));
        config.ownerPid=parser.value(QStringLiteral("async-experiment-owner")).toLongLong(&ownerOk);
        config.skip=parser.value(QStringLiteral("async-experiment-skip")).toInt(&skipOk);
        QString error;
        if (!configured || !ownerOk || !skipOk || !pt::experiment::configure(config,&error)) {
            QTextStream(stderr) << QStringLiteral("实验配置失败：") << error << Qt::endl;
            return 2;
        }
    }
#endif
    pt::MainWindow window;
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
    // 随主窗口寿命保留醒目标记；普通业务标题更新不会抹去该标识。
    window.setWindowIconText(QStringLiteral("独立异步实验构建"));
    window.setWindowTitle(window.windowTitle()+QStringLiteral("【独立异步实验构建】"));
    QObject::connect(&window,&QWidget::windowTitleChanged,&window,[&window](const QString& title) {
        if (!title.endsWith(QStringLiteral("【独立异步实验构建】")))
            window.setWindowTitle(title+QStringLiteral("【独立异步实验构建】"));
    });
#endif
    window.show();
    if (!parser.positionalArguments().isEmpty()) {
        const auto path = parser.positionalArguments().first();
        QTimer::singleShot(0, &window, [&window, path] { window.requestOpenFile(path); });
    }
    if (parser.isSet(QStringLiteral("library"))) {
        const auto path=parser.value(QStringLiteral("library"));
        QTimer::singleShot(0,&window,[&window,path] { window.openLibrary(path); });
    }
    if (parser.isSet(QStringLiteral("netlist"))) {
        const auto path=parser.value(QStringLiteral("netlist"));
        if (parser.positionalArguments().isEmpty()) QTimer::singleShot(0,&window,[&window,path] { window.openNetlist(path); });
        else QObject::connect(&window,&pt::MainWindow::boardLoadFinished,&window,[&window,path](bool success) {
            if (success) window.openNetlist(path);
        },Qt::SingleShotConnection);
    }
    const int exitCode=app.exec();
#ifdef PT_ENABLE_ASYNC_EXPERIMENT
    // 在后台任务退出后关闭记录，避免退出时清掉仍在使用的时钟域。
    QThreadPool::globalInstance()->waitForDone();
    pt::experiment::shutdown();
#endif
    return exitCode;
}
