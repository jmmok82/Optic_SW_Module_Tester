import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

from Common.eventlog import LogEvents
from HR.lens_handler import HRWidget
from Module.Module_Handler import ModuleWidget


def get_resource_path(filename: str) -> Path:
    if getattr(sys, "frozen", False):  # Pyinstaller 실행중이라면
        return Path(sys._MEIPASS) / filename  # 임시폴더 경로 반환
    return Path(__file__).parent / filename  # Vscode 에서는 현재 폴더 반환


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi(str(get_resource_path("OpticLab_UI.ui")), self)
        self.resize(2000, 1000)

        # Load Logger
        self.logger = LogEvents(callback=self.log_event)

        # Load Handler
        self.hr_handler = HRWidget(self, self.logger)
        self.module_handler = ModuleWidget(self, self.logger)

    def on_value_changed(self, text, handler=None):
        sender = self.sender()
        varname = sender.property("varname")

        if not text or text.strip() == "":
            return

        if varname is None:
            self.event_error("Invalid input")
            return
        try:
            try:
                value = float(text)
            except ValueError:
                value = str(text)

            if handler:
                setattr(handler, varname, value)
            else:
                setattr(self, varname, value)

            # self.event_info('set '+str(varname) + ' to ' + str(value))

        except Exception as e:
            self.event_error("Invalid input: %s" % e)
            return

    # Callbacked log function
    def log_event(self, msg):
        self.text_event.append(msg)

    def event_info(self, message):
        self.logger.log_info(message)

    def event_error(self, message):
        self.logger.log_error(message)


if __name__ == "__main__":

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
