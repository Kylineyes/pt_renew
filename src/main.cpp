#include "ui/MainWindow.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QTimer>

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("pt-renew"));
    QCoreApplication::setApplicationVersion(QStringLiteral("0.3.0"));
    QCoreApplication::setOrganizationName(QStringLiteral("PtRenew"));
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("AUTOTRAX 重建工程：菜单、快捷键与 PCB 只读预览。"));
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addPositionalArgument(QStringLiteral("文件"), QStringLiteral("可选：以只读方式打开 PCB FILE 4 板图。"), QStringLiteral("[文件]"));
    parser.process(app);
    if (parser.positionalArguments().size() > 1) parser.showHelp(2);
    pt::MainWindow window;
    window.show();
    if (!parser.positionalArguments().isEmpty()) {
        const auto path = parser.positionalArguments().first();
        QTimer::singleShot(0, &window, [&window, path] { window.requestOpenFile(path); });
    }
    return app.exec();
}
