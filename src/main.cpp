#include "ui/MainWindow.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QCommandLineOption>
#include <QTimer>

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("pt-renew"));
    QCoreApplication::setApplicationVersion(QStringLiteral("0.5.0"));
    QCoreApplication::setOrganizationName(QStringLiteral("PtRenew"));
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("AUTOTRAX 重建工程：板图和封装库的只读查看、检索及测量。"));
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addOption(QCommandLineOption(QStringLiteral("library"),QStringLiteral("在独立只读窗口打开 LIB，不放置到板图。"),QStringLiteral("路径")));
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
    return app.exec();
}
