#include "ui/MainWindow.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QTimer>

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("pt-renew"));
    QCoreApplication::setApplicationVersion(QStringLiteral("0.1.0"));
    QCoreApplication::setOrganizationName(QStringLiteral("PtRenew"));
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("AUTOTRAX 重建工程：菜单、快捷键与只读文件信息探测。"));
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addPositionalArgument(QStringLiteral("文件"), QStringLiteral("可选：探测一个 PCB FILE 4 文件，不载入图元。"), QStringLiteral("[文件]"));
    parser.process(app);
    if (parser.positionalArguments().size() > 1) parser.showHelp(2);
    pt::MainWindow window;
    window.show();
    if (!parser.positionalArguments().isEmpty()) {
        const auto path = parser.positionalArguments().first();
        QTimer::singleShot(0, &window, [&window, path] { window.inspectFile(path); });
    }
    return app.exec();
}
