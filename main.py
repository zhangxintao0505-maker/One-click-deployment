import sys
from PySide6.QtWidgets import QApplication
from ui.toolbox_dialog import ToolboxDialog


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    dialog = ToolboxDialog()
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
