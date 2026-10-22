#include "ui/MainWindow.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QCommandLineOption>
#include <QTimer>

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("pt-renew"));
    QCoreApplication::setApplicationVersion(QStringLiteral("0.8.0"));
    QCoreApplication::setOrganizationName(QStringLiteral("PtRenew"));
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("AUTOTRAX 重建工程：只读板图、库、网表及受限铜层几何分析（非完整 DRC）。"));
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addOption(QCommandLineOption(QStringLiteral("library"),QStringLiteral("在独立只读窗口打开 LIB，不放置到板图。"),QStringLiteral("路径")));
    parser.addOption(QCommandLineOption(QStringLiteral("netlist"),QStringLiteral("只读载入外部 NET；若指定板图则在板图成功载入后映射。"),QStringLiteral("路径")));
    parser.addPositionalArgument(QStringLiteral("文件"), QStringLiteral("可选：以只读方式打开 PCB FILE 4 板图。"), QStringLiteral("[文件]"));
    parser.process(app);
    if (parser.positionalArguments().size() > 1) parser.showHelp(2);
    pt::MainWindow window;
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
    return app.exec();
}
