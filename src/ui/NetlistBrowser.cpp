#include "ui/NetlistBrowser.h"
#include "io/LegacyNetlistReader.h"
#include "geometry/CopperConnectivity.h"
#include <QFileDialog>
#include <QComboBox>
#include <QFutureWatcher>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalBlocker>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QSplitter>
#include <QtConcurrent/QtConcurrentRun>

namespace pt {
NetlistBrowser::NetlistBrowser(QWidget* parent):QDockWidget(QStringLiteral("网表与引脚映射（只读）"),parent) {
    setObjectName(QStringLiteral("netlistDock"));
    auto* content=new QWidget(this);auto* layout=new QVBoxLayout(content);
    auto* buttons=new QHBoxLayout;
    m_open=new QPushButton(QStringLiteral("打开 NET…"),content);m_open->setObjectName(QStringLiteral("netlistOpen"));
    m_clear=new QPushButton(QStringLiteral("移除外部网表"),content);m_clear->setObjectName(QStringLiteral("netlistClear"));
    buttons->addWidget(m_open);buttons->addWidget(m_clear);layout->addLayout(buttons);
    m_copper=new QPushButton(QStringLiteral("受限铜层几何分析（非 DRC）"),content);
    m_copper->setObjectName(QStringLiteral("copperAnalyze"));layout->addWidget(m_copper);
    connect(m_copper,&QPushButton::clicked,this,&NetlistBrowser::runCopperAnalysis);
    m_source=new QComboBox(content);m_source->setObjectName(QStringLiteral("netlistSource"));layout->addWidget(m_source);
    m_status=new QLabel(content);m_status->setObjectName(QStringLiteral("netlistStatus"));m_status->setWordWrap(true);m_status->setTextFormat(Qt::PlainText);layout->addWidget(m_status);
    m_search=new QLineEdit(content);m_search->setObjectName(QStringLiteral("netlistSearch"));m_search->setPlaceholderText(QStringLiteral("按网络名筛选"));m_search->setClearButtonEnabled(true);layout->addWidget(m_search);
    auto* split=new QSplitter(Qt::Vertical,content);
    m_nets=new QListWidget(split);m_nets->setObjectName(QStringLiteral("netlistNets"));
    m_nodes=new QListWidget(split);m_nodes->setObjectName(QStringLiteral("netlistNodes"));
    m_coverageBox=new QWidget(split);m_coverageBox->setObjectName(QStringLiteral("copperCoverageBox"));
    auto* coverageLayout=new QVBoxLayout(m_coverageBox);coverageLayout->setContentsMargins(0,0,0,0);
    m_coverageStatus=new QLabel(m_coverageBox);m_coverageStatus->setObjectName(QStringLiteral("copperCoverageStatus"));
    m_coverageStatus->setWordWrap(true);m_coverageStatus->setTextFormat(Qt::PlainText);coverageLayout->addWidget(m_coverageStatus);
    m_coverageIssues=new QListWidget(m_coverageBox);m_coverageIssues->setObjectName(QStringLiteral("copperCoverageIssues"));
    m_coverageIssues->setAccessibleName(QStringLiteral("未覆盖图元，双击或 Enter 定位"));coverageLayout->addWidget(m_coverageIssues);
    m_coverageBox->hide();
    connect(m_coverageIssues,&QListWidget::itemActivated,this,[this](QListWidgetItem* item) {
        const auto index=item->data(Qt::UserRole).toLongLong();
        if (index>=0) emit primitiveActivated({static_cast<PrimitiveKind>(item->data(Qt::UserRole+1).toInt()),index});
    });
    m_details=new QPlainTextEdit(split);m_details->setObjectName(QStringLiteral("netlistDetails"));m_details->setReadOnly(true);
    split->setSizes({150,100,170,220});layout->addWidget(split,1);setWidget(content);
    connect(m_open,&QPushButton::clicked,this,&NetlistBrowser::chooseFile);
    connect(m_clear,&QPushButton::clicked,this,&NetlistBrowser::clearExternal);
    connect(m_source,&QComboBox::currentIndexChanged,this,[this](int index) {
        if (index>=0 && m_source->itemData(index).toInt()>=0) { m_useExternal=m_source->itemData(index).toInt()==1;rebuild(); }
    });
    connect(m_search,&QLineEdit::textChanged,this,&NetlistBrowser::filter);
    connect(m_nets,&QListWidget::currentRowChanged,this,[this] { showCurrent(); });
    connect(m_nodes,&QListWidget::itemActivated,this,[this](QListWidgetItem* item) {
        const auto pad=item->data(Qt::UserRole).toLongLong();if (pad>=0) emit padActivated(pad);
    });
    rebuild();
}
void NetlistBrowser::setBoard(std::shared_ptr<const BoardDocument> board, bool preserveExternal) {
    ++m_generation;m_board=std::move(board);
    if (!preserveExternal) m_external.reset();
    m_notice = preserveExternal
        ? (m_loading ? QStringLiteral("工作文档已更新；正在读取的 NET 结果已放弃，请重新打开 NET。已有网表已重新映射，旧铜层结论已清除。")
                     : QStringLiteral("工作文档已更新；已有网表已重新映射，旧铜层结论已清除，请重新分析。"))
        : QString();
    m_error.clear();rebuild();
}
void NetlistBrowser::chooseFile() {
    if (m_loading) return;
    const auto path=QFileDialog::getOpenFileName(this,QStringLiteral("只读载入 Protel 网表"),{},QStringLiteral("Protel 网表 (*.net *.NET);;所有文件 (*)"));
    if (!path.isEmpty()) requestFile(path);
}
void NetlistBrowser::requestFile(const QString& path) {
    if (m_loading) return;
    ++m_generation;const auto generation=m_generation;m_error.clear();m_notice.clear();rebuild();
    m_loading=true;m_copper->setEnabled(false);m_open->setEnabled(false);m_clear->setEnabled(true);m_status->setText(QStringLiteral("正在后台读取网表；移除外部网表可放弃结果。"));
    auto* watcher=new QFutureWatcher<NetlistReadResult>(this);
    connect(watcher,&QFutureWatcher<NetlistReadResult>::finished,this,[this,watcher,generation] {
        const auto result=watcher->result();watcher->deleteLater();m_loading=false;m_open->setEnabled(true);
        if (generation==m_generation) apply(result); else rebuild();
    });
    watcher->setFuture(QtConcurrent::run([path] { return LegacyNetlistReader::readFile(path); }));
}
bool NetlistBrowser::loadFile(const QString& path) { if (m_loading) return false; ++m_generation;return apply(LegacyNetlistReader::readFile(path)); }
bool NetlistBrowser::apply(const NetlistReadResult& result) {
    m_external=result.netlist; m_useExternal=true;
    m_error=result.error;m_notice.clear();rebuild();emit netlistLoaded(result.succeeded());return result.succeeded();
}
void NetlistBrowser::clearExternal() { ++m_generation;m_external.reset();m_error.clear();rebuild(); }
void NetlistBrowser::focusSearch() { show();raise();m_search->setFocus(Qt::ShortcutFocusReason);m_search->selectAll(); }
void NetlistBrowser::clearHighlight() {
    m_nets->setCurrentRow(-1);m_nodes->clear();emit padsHighlighted({});
}
void NetlistBrowser::runCopperAnalysis() {
    if (m_analyzing || m_loading || !m_board || !m_active) return;
    m_analyzing=true;const auto generation=++m_copperGeneration;
    m_coverageIssues->clear();m_coverageBox->hide();
    m_copperReport=QStringLiteral("正在后台执行受限铜层几何分析……不是完整 DRC。\n");
    m_copper->setEnabled(false);showCurrent();
    const auto board=m_board;const auto network=m_active;
    auto* watcher=new QFutureWatcher<CopperAnalysis>(this);
    connect(watcher,&QFutureWatcher<CopperAnalysis>::finished,this,[this,watcher,generation,board,network] {
        const auto report=watcher->result();watcher->deleteLater();m_analyzing=false;
        m_copper->setEnabled(m_board!=nullptr && m_active!=nullptr && !m_loading);
        if (generation!=m_copperGeneration || board!=m_board || network!=m_active) return;
        m_copperReport=QStringLiteral("原板图输入 SHA-256：%1\n当前工作文档修订：%2\n网表摘要：%3\n\n")
            .arg(board->sha256).arg(board->workingRevision).arg(network->sha256)+copperAnalysisText(report);
        m_coverageStatus->setText(QStringLiteral("未覆盖图元：%1 条诊断，列出 %2 条；双击或 Enter 定位，隐藏图层不会自动开启。")
            .arg(report.coverageIssueCount).arg(report.coverageIssues.size()));
        for (const auto& issue:report.coverageIssues) {
            auto* item=new QListWidgetItem(copperCoverageIssueText(issue),m_coverageIssues);
            item->setToolTip(item->text());item->setData(Qt::UserRole,qlonglong(issue.primitive.index));
            item->setData(Qt::UserRole+1,static_cast<int>(issue.primitive.kind));
            if (issue.primitive.index<0) item->setFlags(item->flags()&~Qt::ItemIsSelectable);
        }
        m_coverageBox->setVisible(!report.coverageIssues.isEmpty());
        showCurrent();emit copperAnalysisFinished();
    });
    watcher->setFuture(QtConcurrent::run([board,network] { return analyzeCopper(*board,*network); }));
}

void NetlistBrowser::rebuild() {
    ++m_copperGeneration;m_copperReport.clear();
    m_coverageIssues->clear();m_coverageBox->hide();
    emit padsHighlighted({});
    const auto internal=m_board?m_board->embeddedNetlist:nullptr;
    if (!m_external) m_useExternal=false;
    if (!internal && m_external) m_useExternal=true;
    m_active=m_useExternal?m_external:internal;
    {
        QSignalBlocker block(m_source);m_source->clear();
        if (internal) m_source->addItem(QStringLiteral("板内 NETDEF（不与外部自动合并）"),0);
        if (m_external) m_source->addItem(QStringLiteral("外部 NET（不与板内自动合并）"),1);
        if (m_source->count()==0) m_source->addItem(QStringLiteral("尚无网络来源"),-1);
        m_source->setCurrentIndex(qMax(0,m_source->findData(m_useExternal?1:0)));
    }
    m_mapping=m_active?mapNetlist(*m_active,m_board.get()):NetlistMapping();
    m_copper->setEnabled(m_board!=nullptr && m_active!=nullptr && !m_analyzing && !m_loading);
    {QSignalBlocker block(m_nets);m_nets->clear();for (qsizetype i=0;i<m_mapping.nets.size();++i) {
        const auto& net=m_mapping.nets[i];auto* item=new QListWidgetItem(QStringLiteral("%1（%2 显式节点）").arg(net.name).arg(net.nodes.size()),m_nets);item->setData(Qt::UserRole,i);
    }}
    m_clear->setEnabled(m_external!=nullptr || m_loading);
    m_search->clear();filter();showCurrent();
}
void NetlistBrowser::filter() {
    int count=0;QListWidgetItem* first=nullptr;
    for (int i=0;i<m_nets->count();++i) {
        auto* item=m_nets->item(i);const auto index=item->data(Qt::UserRole).toLongLong();
        const bool match=m_mapping.nets[index].name.contains(m_search->text(),Qt::CaseInsensitive);
        item->setHidden(!match);if (match) { ++count;if (!first) first=item; }
    }
    QString text;
    if (m_active) text=QStringLiteral("%1：%2\n网络匹配 %3 / %4；唯一映射 %5，缺失 %6，歧义 %7，冲突节点 %8。\n仅引脚归属映射，不是铜线连通性检查。")
        .arg(m_active->embedded?QStringLiteral("内嵌 NETDEF"):QStringLiteral("外部 NET"),m_active->filePath).arg(count).arg(m_mapping.nets.size())
        .arg(m_mapping.resolved).arg(m_mapping.missing).arg(m_mapping.ambiguous).arg(m_mapping.conflicting);
    else text=QStringLiteral("尚无网表。可打开外部 NET；载入含 NETDEF 的板图后自动查看内嵌网络。");
    if (!m_board && m_active) text.prepend(QStringLiteral("未载入板图：仅查看声明，未执行焊盘映射。\n"));
    if (!m_error.isEmpty()) text.prepend(QStringLiteral("载入失败：%1\n").arg(m_error));
    if (!m_notice.isEmpty()) text.prepend(m_notice+QLatin1Char('\n'));
    m_status->setText(text);
    if (!first) { m_nets->setCurrentRow(-1);showCurrent(); }
    else if (!m_nets->currentItem() || m_nets->currentItem()->isHidden()) m_nets->setCurrentItem(first);
}
void NetlistBrowser::showCurrent() {
    m_nodes->clear();emit padsHighlighted({});
    QString details=QStringLiteral("只读引脚归属映射；未计算铜线实际连通、短路或 DRC。\n"
        "网络名、元件标号和引脚名精确区分大小写匹配；不拆分含多个连字符的标识，冲突/歧义节点不自动高亮。\n");
    if (m_active) {
        details+=QStringLiteral("\n来源摘要：%1\n声明元件：%2\n").arg(m_active->sha256).arg(m_active->components.size());
        for (const auto& warning:m_active->warnings) details+=warning+QLatin1Char('\n');
        for (const auto& issue:m_mapping.diagnostics) details+=issue+QLatin1Char('\n');
    }
    auto* item=m_nets->currentItem();
    if (m_active && item && !item->isHidden()) {
        const auto index=item->data(Qt::UserRole).toLongLong();const auto& net=m_mapping.nets[index];
        QString nodesText=QStringLiteral("网络：%1\n源行：%2\n\n").arg(net.name).arg(m_active->nets[index].sourceLine);
        if (!m_active->nets[index].metadata.isEmpty()) nodesText+=QStringLiteral("附加元数据 %1 字节已保留但未解释。\n").arg(m_active->nets[index].metadata.size());
        for (const auto& node:net.nodes) {
            auto* row=new QListWidgetItem(node.token+QStringLiteral(" — ")+node.status,m_nodes);
            row->setToolTip(QStringLiteral("源行 %1：%2").arg(node.sourceLine).arg(node.status));
            row->setData(Qt::UserRole,node.pads.size()==1&&!node.ambiguous&&!node.conflicting?node.pads.first():qsizetype(-1));
        }
        nodesText+=QStringLiteral("激活唯一匹配节点可居中查看，隐藏图层不会自动开启；高亮只标识焊盘，不绘制代表实际布线的连线。\n\n");
        details.prepend(nodesText);emit padsHighlighted(net.uniquePads);
    }
    if (!m_copperReport.isEmpty()) details=m_copperReport+QStringLiteral("\n\n网表映射信息：\n")+details;
    m_details->setPlainText(details);
}
}
