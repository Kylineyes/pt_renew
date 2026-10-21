#pragma once
#include "domain/FootprintLibrary.h"
#include <QDialog>

class QListWidget;
class QLineEdit;
class QLabel;
class QPushButton;
class QPlainTextEdit;

namespace pt {
class BoardCanvas;

class LibraryBrowser final : public QDialog {
    Q_OBJECT
public:
    explicit LibraryBrowser(QWidget* parent=nullptr);
    void showBrowser();
    void chooseFile();
    void requestLibrary(const QString& path);
    bool loadLibrary(const QString& path);
    void clearLibrary();
    const FootprintLibrary* library() const { return m_library.get(); }
signals:
    void libraryLoaded(bool succeeded);
private:
    bool applyLibrary(const LibraryReadResult& result);
    void filterEntries();
    void previewCurrent();
    void updateDetails();
    std::shared_ptr<const FootprintLibrary> m_library;
    BoardCanvas* m_preview=nullptr;
    QListWidget* m_list=nullptr;
    QLineEdit* m_search=nullptr;
    QLabel* m_status=nullptr;
    QPushButton* m_open=nullptr;
    QPushButton* m_close=nullptr;
    QPlainTextEdit* m_details=nullptr;
    qsizetype m_current=-1;
    quint64 m_generation=0;
    bool m_loading=false;
};

}
