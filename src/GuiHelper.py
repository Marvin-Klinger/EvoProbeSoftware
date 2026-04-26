from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt


# this file aims to provide useful functions when handling pyqt stuff

def get_data_from_widget(widget: qtw.QWidget):
    match type(widget):
        case qtw.QComboBox:
            return widget.currentData()
        case qtw.QCheckBox:
            return widget.isChecked()
        case qtw.QLineEdit:
            return widget.text()
        case qtw.QSpinBox | qtw.QDoubleSpinBox:
            return widget.value()
        case qtw.QTextEdit:
            return widget.toPlainText()
        case _:
            return widget


def get_save_data_from_widget(widget: qtw.QWidget):
    match type(widget):
        case qtw.QComboBox:
            return widget.currentIndex()
        case qtw.QCheckBox:
            return widget.isChecked()
        case qtw.QLineEdit:
            return widget.text()
        case qtw.QSpinBox | qtw.QDoubleSpinBox:
            return widget.value()
        case _:
            return None


def cascade_get_save_data(obj):
    if isinstance(obj, qtw.QWidget):
        return get_save_data_from_widget(obj)
    elif isinstance(obj, list):
        return [cascade_get_save_data(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: cascade_get_save_data(v) for k, v in obj.items()}
    else:
        return None


def change_widget_with_data(widget: qtw.QWidget, data):
    match type(widget):
        case qtw.QComboBox:
            widget.setCurrentIndex(data)
        case qtw.QCheckBox:
            widget.setChecked(data)
        case qtw.QLineEdit:
            widget.setText(data)
        case qtw.QSpinBox | qtw.QDoubleSpinBox:
            widget.setValue(data)
        case _:
            pass


def cascade_change_with_data(obj, data):
    if isinstance(obj, qtw.QWidget):
        change_widget_with_data(obj, data)
    elif isinstance(obj, list) and isinstance(data, list):
        for i in range(len(obj)):
            try:
                cascade_change_with_data(obj[i], data[i])
            except IndexError:
                pass
    elif isinstance(obj, dict) and isinstance(data, dict):
        for k, v in obj.items():
            try:
                cascade_change_with_data(v, data[k])
            except KeyError:
                pass
    else:
        pass
