import sys
import os
import pathlib
from PyQt5 import QtGui, QtCore, QtWidgets

from function import convert_to_mp4, get_sequence


class Thread(QtCore.QThread):
    signal_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent, path: str):
        super().__init__(parent)
        self.path = path

    def run(self):
        self.signal_data.emit(get_sequence(self.path))


class ThreadConvert(QtCore.QThread):
    signal_complete = QtCore.pyqtSignal(bool)

    def __init__(self, parent, data: list):
        super().__init__(parent)
        self.data = data

    def run(self):
        for frames in self.data:
            convert_to_mp4(**frames)
        self.signal_complete.emit(True)


class LoadRingWidget(QtWidgets.QWidget):
    def __init__(self, parent, color, ring_offset_x, ring_offset_y, max_size):
        super().__init__(parent)
        self.parent = parent

        self.max_size = max_size
        self.setMaximumSize(*max_size)
        self.setMinimumSize(*max_size)

        self.ring_offset_x = ring_offset_x
        self.ring_offset_y = ring_offset_y
        self.color = QtGui.QColor(100, 255, 100, 200) if color is None else QtGui.QColor(*color)

        self.angle = 0
        self.len_arc = 0
        self.flag_direction = False
        self.flag_start = True

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_angle)

    def update_angle(self):
        if self.len_arc in (0, 360):
            self.flag_direction = not self.flag_direction

        self.len_arc += 5 if self.flag_direction else -5
        self.angle += 5 if self.flag_direction else 10

        self.update()  # вызываем перерисовку виджета

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(100, 255, 100, 200)
        pen = QtGui.QPen(color, self.width()*0.15, QtCore.Qt.SolidLine)
        bruh = QtGui.QBrush(color)
        painter.setPen(pen)
        painter.setBrush(bruh)

        ring_offset_x = self.max_size[0] * self.ring_offset_x
        ring_offset_y = self.max_size[1] * self.ring_offset_y
        ring_width = self.max_size[0] * (1 - self.ring_offset_x * 2)
        ring_height = self.max_size[1] * (1 - self.ring_offset_y * 2)
        rect_ring = (ring_offset_x, ring_offset_y, ring_width, ring_height)
        painter.drawArc(QtCore.QRectF(*rect_ring), self.angle * 16, self.len_arc * 16)

    def start_load(self):
        self.timer.start(30)  # обновляем каждые 30 миллисекунд для плавной анимации

    def stop_load(self):
        self.timer.stop()


class LoadRing(QtWidgets.QWidget):
    def __init__(self, parent, color=None, ring_offset_x=0.2, ring_offset_y=0.2, max_size=(25, 25)):
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setMaximumSize(*max_size)
        self.setMinimumSize(*max_size)

        self.label_icon_ok = QtWidgets.QLabel(self)
        pixpmap = QtGui.QPixmap(os.path.join(os.getcwd(), 'resources/icon/load_ok.png'))
        self.label_icon_ok.setPixmap(pixpmap)
        self.label_icon_ok.setScaledContents(True)
        self.label_icon_ok.setMaximumSize(*(int(m * (1 - ring_offset_x)) for m in max_size))
        self.label_icon_ok.setMinimumSize(*(int(m * (1 - ring_offset_y)) for m in max_size))
        self.label_icon_ok.setMargin(2)
        layout.addWidget(self.label_icon_ok)

        self.load_ring_widget = LoadRingWidget(self, color=color,
                                               ring_offset_x=ring_offset_x, ring_offset_y=ring_offset_y,
                                               max_size=max_size)
        self.load_ring_widget.setMaximumSize(*max_size)
        layout.addWidget(self.load_ring_widget)

    def start_load(self):
        self.load_ring_widget.show()
        self.label_icon_ok.hide()
        self.load_ring_widget.start_load()

    def stop_load(self):
        self.load_ring_widget.hide()
        self.label_icon_ok.show()
        self.load_ring_widget.stop_load()


class LabelFilePath(QtWidgets.QLabel):
    signal_choose_file = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        self.setObjectName('label')

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        dlg = QtWidgets.QFileDialog()
        folderpath = dlg.getExistingDirectory(self, 'Выберете папку').replace('/', '\\')
        if folderpath:
            self.setText(folderpath)
            self.setToolTip(folderpath)
            self.signal_choose_file.emit(folderpath)


class FrameInputFiles(QtWidgets.QGroupBox):
    signal_choose_file = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

        self.setTitle('Выбор файла')
        self.setObjectName('FrameInputFiles')

        self.h_layout = QtWidgets.QHBoxLayout(self)
        self.h_layout.setSpacing(0)

        self.label_path = LabelFilePath(self)
        self.label_path.signal_choose_file.connect(self.click_label)
        self.label_path.setObjectName('label_path')

        self.label_path.setText('Выберите путь...')
        self.h_layout.addWidget(self.label_path)

        self.load_ring = LoadRing(self)
        self.h_layout.addWidget(self.load_ring)

    def click_label(self, path: str) -> None:
        self.signal_choose_file.emit(path)


class FrameItem(QtWidgets.QFrame):
    signal_del_item = QtCore.pyqtSignal(QtWidgets.QFrame)

    def __init__(self, parent, seq_name: str, count_file: int, pattern: str, root: str, suffix: str, start_number: int):
        super().__init__(parent)

        self.setObjectName('fframe')
        self.setStyleSheet("""
        #fframe {
        background-color: white;
        border-radius: 10px;
        }
        """)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self, blurRadius=5, xOffset=3, yOffset=3)
        self.setGraphicsEffect(shadow)

        self.seq_name = seq_name
        self.fps = 24
        self.count_file = str(count_file)
        self.pattern = pattern
        self.root = root
        self.suffix = suffix
        self.start_number = start_number

        self.setMinimumSize(0, 105)
        self.setMaximumSize(100000, 105)

        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(5, 5, 5, 5)
        self.grid.setSpacing(3)

        self.check_box = QtWidgets.QCheckBox(self)
        self.check_box.setText(self.seq_name)
        self.check_box.clicked.connect(self.set_state)
        self.grid.addWidget(self.check_box, 0, 0, 1, 1)

        self.btn_del_item = QtWidgets.QPushButton(self)
        self.btn_del_item.setMinimumSize(15, 15)
        self.btn_del_item.setMaximumSize(15, 15)
        self.btn_del_item.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_del_item.setText('x')
        self.btn_del_item.setObjectName('btn_del_item')
        self.btn_del_item.setStyleSheet("""
        #btn_del_item {
        border-radius: 7px;
        }
        #btn_del_item:hover {
        background-color: rgba(255, 0, 0, 50);
        border: 1px solid black;
        }
        """)
        self.btn_del_item.clicked.connect(self.del_item)
        self.grid.addWidget(self.btn_del_item, 0, 1, 1, 1)

        self.frame_info = QtWidgets.QFrame(self)
        self.frame_info.setContentsMargins(0, 0, 0, 0)
        self.frame_info.setObjectName('frame_info')
        self.frame_info.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.grid.addWidget(self.frame_info, 1, 0, 1, 2)

        self.grid_frame_info = QtWidgets.QGridLayout(self.frame_info)
        self.grid_frame_info.setSpacing(5)

        self.label_name_q_frame = QtWidgets.QLabel(self.frame_info)
        self.label_name_q_frame.setText('Файлов: ')
        self.grid_frame_info.addWidget(self.label_name_q_frame, 0, 0, 1, 1)

        self.label_q_frame = QtWidgets.QLabel(self.frame_info)
        self.label_q_frame.setText(self.count_file)
        self.grid_frame_info.addWidget(self.label_q_frame, 0, 1, 1, 1)

        self.label_filename = QtWidgets.QLabel(self.frame_info)
        self.label_filename.setText('Имя файла:')
        self.grid_frame_info.addWidget(self.label_filename, 1, 0, 1, 1)

        self.lineedit_out_name = QtWidgets.QLineEdit(self.frame_info)
        self.lineedit_out_name.setText(self.seq_name)
        self.lineedit_out_name.setObjectName('lineedit_out_name')
        self.lineedit_out_name.setStyleSheet("""
        #lineedit_out_name {
        border: 1px solid black;
        border-radius: 3px
        }
        """)
        self.grid_frame_info.addWidget(self.lineedit_out_name, 1, 1, 1, 1)

        self.label_fps = QtWidgets.QLabel(self.frame_info)
        self.label_fps.setText('FPS')
        self.grid_frame_info.addWidget(self.label_fps, 1, 2, 1, 1)

        self.lineedit_fps = QtWidgets.QLineEdit(self.frame_info)
        self.lineedit_fps.setText(str(self.fps))
        self.lineedit_fps.setObjectName('lineedit_fps')
        self.lineedit_fps.setStyleSheet("""
        #lineedit_fps {
        border: 1px solid black;
        border-radius: 3px
        }
        """)
        self.lineedit_fps.setMaximumSize(25, 30)
        self.grid_frame_info.addWidget(self.lineedit_fps, 1, 3, 1, 1)

        self.label_filepath = QtWidgets.QLabel(self.frame_info)
        self.label_filepath.setText('Вывод:')
        self.grid_frame_info.addWidget(self.label_filepath, 3, 0, 1, 1)

        self.outfilepath = LabelFilePath(self.frame_info)
        self.outfilepath.setText(os.path.join(os.getcwd(), 'result'))
        self.grid_frame_info.addWidget(self.outfilepath, 3, 1, 1, 3)

    def setCheckState(self, state):
        self.check_box.setCheckState(state)
        self.set_state(True)

    def set_state(self, event) -> None:
        if not self.check_box.checkState():
            self.setStyleSheet("""
            #fframe {
            background-color: white;
            border-radius: 10px;
            }
            """)
        else:
            self.setStyleSheet("""
            #fframe {
            background-color: white;
            border-radius: 10px;
            border: 1px solid black;
            }
            """)

    def get_data(self) -> dict:
        if self.check_box.checkState():
            return {
                'seq_name': self.seq_name,
                'root': self.root,
                'out_path': self.outfilepath.text(),
                'out_name': self.lineedit_out_name.text(),
                'fps': self.lineedit_fps.text(),
                'pattern': self.pattern,
                'suffix': self.suffix,
                'start_number': self.start_number
            }

    def del_item(self, event):
        self.parent().update()
        self.signal_del_item.emit(self)


class FrameOutputFiles(QtWidgets.QGroupBox):
    signal_items_empty = QtCore.pyqtSignal(bool)

    def __init__(self, parent):
        super().__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet('FrameOutputFiles')
        self.items = []

        self.setTitle('Найденные файлы')
        self.v_layout = QtWidgets.QVBoxLayout(self)
        self.v_layout.setSpacing(5)

        self.main_check_box = QtWidgets.QCheckBox(self)
        self.main_check_box.setText('Выбрать все')
        self.main_check_box.clicked.connect(self.click_checkbox)
        self.v_layout.addWidget(self.main_check_box)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setObjectName('scroll_area')
        self.scroll_area.setStyleSheet("""
        #scroll_area {
        border: none;
        background-color: #EBECF1;
        }
        """)

        self.scroll_widget = QtWidgets.QWidget(self.scroll_area)
        self.scroll_widget.setObjectName('scroll_widget')
        self.scroll_widget.setStyleSheet("""
        #scroll_widget {
        border: none;
        background-color: #EBECF1;
        }
        """)

        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.v_layout.addWidget(self.scroll_area)

        self.v_layout_scroll_box = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.v_layout_scroll_box.setSpacing(5)

    def fill(self, data: dict):
        self.clear()
        try:
            self.v_layout_scroll_box.removeItem(self.spacer)
        except AttributeError:
            ...

        for seq_name, value in data.items():
            item = FrameItem(self.scroll_widget, seq_name=seq_name, **value)
            item.signal_del_item.connect(self.del_item)
            self.v_layout_scroll_box.addWidget(item)
            self.items.append(item)

        self.spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.v_layout_scroll_box.addItem(self.spacer)

    def clear(self):
        for item in self.items:
            self.v_layout.removeWidget(item)
        self.items.clear()

        try:
            self.v_layout_scroll_box.removeItem(self.spacer)
        except AttributeError:
            ...
        self.signal_items_empty.emit(True)

    def click_checkbox(self, event):
        for item in self.items:
            item.setCheckState(self.main_check_box.checkState())

    def get_data(self) -> list:
        data = []
        for item in self.items:
            data_item = item.get_data()
            if data_item:
                data.append(data_item)
        return data

    def del_item(self, widgets: QtWidgets.QFrame):
        self.v_layout.removeWidget(widgets)
        self.items.pop(self.items.index(widgets))

        if not self.items:
            self.v_layout_scroll_box.removeItem(self.spacer)
            self.signal_items_empty.emit(True)


class FrameToMp4(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_window()
        self.init_widget()

    def init_window(self):
        # self.resize(500, 50)
        self.setWindowTitle('ConvertFrameToMp4')

        self.setObjectName('main')
        self.setStyleSheet("""
        #main {
        background-color: #EBECF1;
        }
        """)

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.grid = QtWidgets.QGridLayout(self.centralwidget)
        self.grid.setContentsMargins(5, 5, 5, 5)
        self.grid.setObjectName("gridLayoutCentral")

        self.setCentralWidget(self.centralwidget)

    def init_widget(self):
        self.frame_input_files = FrameInputFiles(self)
        self.frame_input_files.signal_choose_file.connect(self.__fill)
        self.grid.addWidget(self.frame_input_files)

        self.frame_output_files = FrameOutputFiles(self)
        self.frame_output_files.signal_items_empty.connect(self.items_empty)
        self.grid.addWidget(self.frame_output_files)

        self.btn_start = QtWidgets.QPushButton(self)
        self.btn_start.setText('ОК')
        self.btn_start.setMinimumSize(0, 20)
        self.btn_start.setObjectName('btn_start')
        self.btn_start.setStyleSheet("""
        #btn_start {
        border: 1px solid black;
        border-radius: 5px;
        }
        #btn_start:hover {
        background-color: #BEDAE5;
        }
        """)
        self.btn_start.clicked.connect(self.convert_to_mp4)
        self.grid.addWidget(self.btn_start)

        self.items_empty(True)

    def __fill(self, path):
        thread = Thread(self, path)
        thread.signal_data.connect(self.fill)
        thread.start()

    def fill(self, data: dict) -> None:
        if data:
            self.frame_output_files.fill(data)
            self.frame_output_files.show()
            self.btn_start.show()
            self.resize(500, 450)

            self.frame_input_files.load_ring.stop_load()

    def convert_to_mp4(self):
        out_path = os.path.join(os.getcwd(), 'result')
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        self.frame_input_files.load_ring.start_load()
        data = self.frame_output_files.get_data()
        thread = ThreadConvert(self, data)
        thread.signal_complete.connect(lambda event: self.frame_input_files.load_ring.stop_load())
        thread.start()

    def items_empty(self, value: bool):
        self.frame_output_files.hide()
        self.btn_start.hide()
        self.resize(450, 65)


if __name__ == '__main__':
    # get_frames(os.getcwd())
    # seq = filename_to_sequence('fire blood 002.jpt')
    # print(seq)
    app = QtWidgets.QApplication(sys.argv)

    window = FrameToMp4()
    window.show()
    sys.exit(app.exec_())