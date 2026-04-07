import sys
import os
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListWidget, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QListWidgetItem, 
                             QMessageBox, QPushButton, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint

class LainExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.custom_dir = None
        # Настройка Окна
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("NAVI System v0.3")
        self.resize(800, 600)
        # Убираем рамку
        self.setWindowFlags(Qt.FramelessWindowHint) 
        
        # СТИЛЬ
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent; 
            }

            #central_widget {
                background-color: #0a0a0a;
                border: 1px solid #330000;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }

            QLabel { 
                color: #d40404; 
                font-family: 'Courier New'; 
            }
            
            #custom_title_bar {
                background-color: #050505;
                border-bottom: 1px solid #330000;
                height: 25px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            

            QPushButton#btn_close {
                background-color: transparent;
                color: #ff0000;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 5px 10px;
            }

            QPushButton#btn_close:hover {
                background-color: #ff0000;
                color: black;
                border-top-right-radius: 10px;
            }
            
            QPushButton#btn_min {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 16px;
                padding: 5px 10px;
            }
            
            QPushButton#btn_min:hover {
                background-color: #330000;
                color: white;
            }

            QListWidget {
                background-color: #050505;
                color: #a0a0a0;
                font-family: 'Courier New';
                border: none;
                font-size: 14px;
            }
            
            QListWidget::item:selected { 
                background-color: #330000; 
                color: #ffff00; 
            }
            
            QScrollBar:vertical {
                border: none;
                background: #0a0a0a;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #550000;
                min-height: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical:hover { 
                background: #ff0000; 
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
                height: 0px;
                background: transparent;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        # ГЛАВНОЕ ОКНО
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0) # Убираем отступы по краям
        layout.setSpacing(0) # Убираем расстояние между элементами

        # РАМКА ОКНА СВЕРХУ (TITLE BAR)
        self.title_bar = QWidget()
        self.title_bar.setObjectName("custom_title_bar") # Для стиля выше
        self.title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)

        # Текст слева
        self.label_status = QLabel("NAVI [Nomad Ambitious Vibecoded Interface]")
        
        self.target_drive = os.path.splitdrive(sys.executable)[0] #Узнаём диск на котором запущен
        # self.target_drive = "E:" # Для тестов
        self.label_status.setText(f"{self.label_status.text()[:42]} {self.target_drive}")
        title_layout.addWidget(self.label_status)
        
        # "Пружина", чтобы сдвинуть кнопки вправо
        title_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Кнопка Свернуть
        self.btn_min = QPushButton("_")
        self.btn_min.setObjectName("btn_min")
        self.btn_min.setFixedSize(40, 30)
        self.btn_min.clicked.connect(self.showMinimized) # Стандартная функция сворачивания
        title_layout.addWidget(self.btn_min)

        # Кнопка Закрыть
        self.btn_close = QPushButton("X")
        self.btn_close.setObjectName("btn_close")
        self.btn_close.setFixedSize(40, 30)
        self.btn_close.clicked.connect(self.close) # Стандартная функция закрытия
        title_layout.addWidget(self.btn_close)

        # Добавляем рамку в главный лайаут
        layout.addWidget(self.title_bar)

        # ОБЛАСТЬ С ФАЙЛАМИ
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.file_list)
        
        self.start_watcher()
        self.load_files()

    # МЕТОДЫ ДЛЯ ПЕРЕТАСКИВАНИЯ ОКНА
    def mousePressEvent(self, event):
        # Запоминаем позицию клика, если он был на нашей рамке
        if event.button() == Qt.LeftButton and event.y() <= 30:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        else:
            self.drag_pos = None

    def mouseMoveEvent(self, event):
        # Если зажата ЛКМ и есть позиция старта -> двигаем окно
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos') and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def load_files(self,custom_dir=None):
        """Показывает файлы, скрывая только саму программу"""
        self.file_list.clear()
        if getattr(sys, 'frozen', False):
            # Программа собрана в exe
            current_filename = os.path.basename(sys.executable)
        else:
            # Запущен как обычный скрипт .py
            current_filename = os.path.basename(sys.argv[0])

        try:
            if custom_dir == None: custom_dir = self.target_drive + "\\"
            files = os.listdir(custom_dir)
            self.file_list.addItem(self.target_drive + "\\")
            if self.target_drive == 'C:': 
                pass
                #self.file_list.addItem('C:\\Users\\DNS\\Desktop') FIXME сделать проверку имерни пользователя и вставить сюда

            for f in files:
                if f == current_filename:
                    continue
                # (Опционально) Можно также скрыть системные папки, типа $RECYCLE.BIN или System Volume Information
                #if f.startswith('$') or f == 'System Volume Information':
                #    continue

                item = QListWidgetItem(f)

                if os.path.isdir(os.path.join(custom_dir, f)):
                    item.setForeground(Qt.red)
                
                self.file_list.addItem(item)
                
        except Exception as e:
            self.label_status.setText(f"Error reading data: {e}")

    def open_file(self, item):
        """Открывает файл, папку"""
        file_name = item.text()
        if self.custom_dir == None: self.custom_dir = self.target_drive + "\\"
        full_path = os.path.join(self.custom_dir, file_name)
        print(full_path)
        if os.path.isfile(full_path):
            os.startfile(full_path)
        elif os.path.isdir(full_path):
            self.custom_dir = full_path
            self.label_status.setText(f"{self.label_status.text()[:42]} {full_path}")
            self.load_files(full_path)

    # === 4. Страж (Убийца процесса) ===
    def start_watcher(self):
        def watch_loop():
            while True:
                if not os.path.exists(self.target_drive):
                    print("DRIVE LOST. TERMINATING...")

                    os._exit(0)
                time.sleep(1)
        
        thread = threading.Thread(target=watch_loop, daemon=True)
        thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LainExplorer()
    window.show()
    sys.exit(app.exec_())