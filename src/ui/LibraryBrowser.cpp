#include "ui/LibraryBrowser.h"
#include "io/LegacyLibraryReader.h"
#include "ui/BoardCanvas.h"
#include "geometry/BoardGeometry.h"
#include <QAction>
#include <QFileDialog>
#include <QFutureWatcher>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QShortcut>
#include <QSignalBlocker>
#include <QSplitter>
#include <QVBoxLayout>
#include <QtConcurrent/QtConcurrentRun>

namespace pt {
LibraryBrowser::LibraryBrowser(QWidget* parent) : QDialog(parent) {
    setWindowTitle(QStringLiteral("LIB 封装库只读浏览"));
    setObjectName(QStringLiteral("libraryBrowser"));
    resize(1200,760);
    auto* layout=new QVBoxLayout(this);
    auto* toolbar=new QHBoxLayout;
    m_open=new QPushButton(QStringLiteral("打开 LIB…"),this); m_open->setObjectName(QStringLiteral("libraryOpen"));
    m_close=new QPushButton(QStringLiteral("关闭当前库"),this); m_close->setObjectName(QStringLiteral("libraryClose"));
    toolbar->addWidget(m_open); toolbar->addWidget(m_close);
    auto* zoomOut=new QPushButton(QStringLiteral("缩小"),this);
    auto* fit=new QPushButton(QStringLiteral("适配"),this);
    auto* zoomIn=new QPushButton(QStringLiteral("放大"),this);
    toolbar->addStretch(); toolbar->addWidget(zoomOut); toolbar->addWidget(fit); toolbar->addWidget(zoomIn);
    layout->addLayout(toolbar);
    m_status=new QLabel(this); m_status->setObjectName(QStringLiteral("libraryStatus")); m_status->setWordWrap(true);
    m_status->setTextFormat(Qt::PlainText); m_status->setSizePolicy(QSizePolicy::Preferred,QSizePolicy::Maximum);
    m_status->setMaximumHeight(100);
    layout->addWidget(m_status);
    auto* split=new QSplitter(this);
    auto* left=new QWidget(split); auto* leftLayout=new QVBoxLayout(left);
    m_search=new QLineEdit(left); m_search->setObjectName(QStringLiteral("librarySearch"));
    m_search->setPlaceholderText(QStringLiteral("按名称筛选；Ctrl+F")); m_search->setClearButtonEnabled(true);
    m_list=new QListWidget(left); m_list->setObjectName(QStringLiteral("libraryEntries"));
    leftLayout->addWidget(m_search); leftLayout->addWidget(m_list);
    auto* right=new QSplitter(Qt::Vertical,split);
    m_preview=new BoardCanvas(right); m_preview->setObjectName(QStringLiteral("libraryPreview"));
    m_details=new QPlainTextEdit(right); m_details->setObjectName(QStringLiteral("libraryDetails")); m_details->setReadOnly(true);
    m_details->setMinimumHeight(140);
    split->addWidget(left); split->addWidget(right); split->setStretchFactor(1,1); split->setSizes({300,900});
    right->setStretchFactor(0,3); right->setStretchFactor(1,1);
    right->setSizes({500,220}); layout->addWidget(split,1);
    connect(m_open,&QPushButton::clicked,this,&LibraryBrowser::chooseFile);
    connect(m_close,&QPushButton::clicked,this,&LibraryBrowser::clearLibrary);
    connect(m_search,&QLineEdit::textChanged,this,&LibraryBrowser::filterEntries);
    connect(m_list,&QListWidget::currentRowChanged,this,[this] { previewCurrent(); });
    connect(m_preview,&BoardCanvas::selectionChanged,this,&LibraryBrowser::updateDetails);
    connect(zoomOut,&QPushButton::clicked,m_preview,&BoardCanvas::zoomOut);
    connect(zoomIn,&QPushButton::clicked,m_preview,&BoardCanvas::zoomIn);
    connect(fit,&QPushButton::clicked,m_preview,&BoardCanvas::resetView);
    auto* find=new QShortcut(QKeySequence::Find,this);
    connect(find,&QShortcut::activated,this,[this] { m_search->setFocus(); m_search->selectAll(); });
    auto* open=new QShortcut(QKeySequence::Open,this); connect(open,&QShortcut::activated,this,&LibraryBrowser::chooseFile);
    auto* clear=new QAction(this); clear->setShortcut(QKeySequence(Qt::Key_Escape));
    clear->setShortcutContext(Qt::WidgetShortcut); m_preview->addAction(clear);
    connect(clear,&QAction::triggered,m_preview,&BoardCanvas::clearSelection);
    connect(m_preview,&BoardCanvas::selectionChanged,this,[this,clear] { clear->setEnabled(m_preview->selection().has_value()); });
    clearLibrary();
}

void LibraryBrowser::showBrowser() { show(); raise(); activateWindow(); }
void LibraryBrowser::chooseFile() {
    if (m_loading) return;
    showBrowser();
    const auto path=QFileDialog::getOpenFileName(this,QStringLiteral("打开旧封装库（只读）"),{},QStringLiteral("AUTOTRAX 封装库 (*.lib *.LIB);;所有文件 (*)"));
    if (!path.isEmpty()) requestLibrary(path);
}

void LibraryBrowser::requestLibrary(const QString& path) {
    if (m_loading) return;
    clearLibrary();
    m_loading=true; const auto generation=++m_generation;
    m_open->setEnabled(false); m_close->setEnabled(true); m_status->setText(QStringLiteral("正在后台验证目录及解码封装；关闭当前库可放弃结果。"));
    auto* watcher=new QFutureWatcher<LibraryReadResult>(this);
    connect(watcher,&QFutureWatcher<LibraryReadResult>::finished,this,[this,watcher,generation] {
        const auto result=watcher->result(); watcher->deleteLater();
        m_loading=false; m_open->setEnabled(true);
        if (generation==m_generation) applyLibrary(result);
        else if (!m_library) m_status->setText(QStringLiteral("库已关闭，可重新打开。"));
        m_close->setEnabled(m_library!=nullptr);
    });
    watcher->setFuture(QtConcurrent::run([path] { return LegacyLibraryReader::readFile(path); }));
}

bool LibraryBrowser::loadLibrary(const QString& path) {
    if (m_loading) return false;
    return applyLibrary(LegacyLibraryReader::readFile(path));
}

bool LibraryBrowser::applyLibrary(const LibraryReadResult& result) {
    clearLibrary();
    if (!result.succeeded()) {
        m_status->setText(QStringLiteral("库载入失败：%1").arg(result.error)); emit libraryLoaded(false); return false;
    }
    m_library=result.library;
    {
        QSignalBlocker block(m_list);
        for (qsizetype i=0;i<m_library->entries.size();++i) {
            const auto& entry=m_library->entries[i];
            auto* item=new QListWidgetItem(QStringLiteral("%1  [槽 %2]%3").arg(entry.name).arg(entry.slot+1)
                .arg(entry.preview?QString():QStringLiteral("（不可预览）")),m_list);
            item->setData(Qt::UserRole,i);
        }
    }
    m_close->setEnabled(true); filterEntries(); previewCurrent(); emit libraryLoaded(true); return true;
}

void LibraryBrowser::clearLibrary() {
    ++m_generation; m_current=-1; m_library.reset();
    m_list->clear(); m_search->clear();
    m_preview->setDocument(nullptr); m_preview->hide();
    m_close->setEnabled(m_loading);
    m_status->setText(m_loading?QStringLiteral("已放弃读取结果，待当前任务结束后可重新打开。"):QStringLiteral("尚未打开 LIB。库预览与主板图独立，不放置元件、不保存。"));
    m_details->setPlainText(QStringLiteral("仅支持已观测的 PCB 4 LIBRARY 二进制布局。\n未知图元或损坏条目会明确拒绝预览，不跳过后显示不完整封装。"));
}

void LibraryBrowser::filterEntries() {
    if (!m_library) return;
    int matches=0,valid=0; QListWidgetItem* first=nullptr;
    for (int i=0;i<m_list->count();++i) {
        auto* item=m_list->item(i); const auto& entry=m_library->entries[item->data(Qt::UserRole).toLongLong()];
        const bool match=entry.name.contains(m_search->text(),Qt::CaseInsensitive);
        item->setHidden(!match); if (match) { ++matches; if (!first) first=item; }
        if (entry.preview) ++valid;
    }
    m_status->setText(QStringLiteral("%1\n匹配 %2 / %3 个条目；可预览 %4；未分配槽 %5（其中残留名称 %6）。只读，未放置到主板图。")
        .arg(m_library->filePath).arg(matches).arg(m_library->entries.size()).arg(valid)
        .arg(m_library->unallocatedSlots).arg(m_library->retainedNameSlots));
    if (!m_list->currentItem() || m_list->currentItem()->isHidden()) m_list->setCurrentItem(first);
    if (!first) { m_list->setCurrentRow(-1); previewCurrent(); }
}

void LibraryBrowser::previewCurrent() {
    auto* item=m_list->currentItem();
    const qsizetype current=item&&!item->isHidden()?item->data(Qt::UserRole).toLongLong():-1;
    if (current==m_current) { updateDetails(); return; }
    m_current=current;
    const bool valid=m_library && m_current>=0 && m_current<m_library->entries.size();
    const auto doc=valid?m_library->entries[m_current].preview:nullptr;
    m_preview->setDocument(doc); m_preview->setVisible(doc!=nullptr);
    updateDetails();
}

void LibraryBrowser::updateDetails() {
    if (!m_library || m_current<0 || m_current>=m_library->entries.size()) {
        if (m_library) m_details->setPlainText(QStringLiteral("暂无匹配条目或尚未选择封装。"));
        return;
    }
    const auto& entry=m_library->entries[m_current];
    QString text=QStringLiteral("库：%1\n库 SHA-256：%2\n封装：%3\n目录槽：%4\n起始记录：%5（字节偏移 0x%6）\n声明图元：%7\n")
        .arg(m_library->filePath,m_library->sha256,entry.name).arg(entry.slot+1).arg(entry.firstRecord)
        .arg(quint64(entry.firstRecord)*16,0,16).arg(entry.primitiveCount);
    if (!entry.preview) text+=QStringLiteral("\n禁止预览：%1\n").arg(entry.error);
    else {
        const auto& b=*entry.preview;
        text+=QStringLiteral("读取至记录：%1\n走线 %2，焊盘 %3，过孔 %4，圆弧 %5，填充 %6，文字 %7。\n")
            .arg(entry.endRecord).arg(b.tracks.size()).arg(b.pads.size()).arg(b.vias.size()).arg(b.arcs.size()).arg(b.fills.size()).arg(b.texts.size());
        for (const auto& warning : b.warnings) text+=warning+QLatin1Char('\n');
        if (m_preview->selection()) text=QStringLiteral("选中图元（来源按字节偏移，不是文本行）：\n")+primitiveDescription(b,*m_preview->selection())+QStringLiteral("\n\n库与封装摘要：\n")+text;
    }
    m_details->setPlainText(text);
}
}
