#!/usr/bin/env python

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QMessageBox
import subprocess


class Application(QWidget):
    def __init__(self):
        super().__init__()

        self.SAMPLE_RATES = (44100, 48000, 88200, 96000)
        self.BUFFER_SIZES = (32, 64, 128, 256, 512, 1024)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Pipewire Sample Rate Settings')
        self.setGeometry(100, 100, 350, 200)

        layout = QVBoxLayout()

        self.message = QLabel("Sample Rate")
        layout.addWidget(self.message)

        self.sampleRateComboBox = QComboBox()
        self.updateSampleRates()

        # Set current sample rate or indicate unknown
        current_rate = self.read('rate')
        if current_rate == "Unknown":
            self.sampleRateComboBox.addItem(current_rate)
            self.sampleRateComboBox.setCurrentIndex(self.sampleRateComboBox.findText(current_rate))
        else:
            current_rate_index = self.sampleRateComboBox.findText(current_rate)
            if current_rate_index >= 0:
                self.sampleRateComboBox.setCurrentIndex(current_rate_index)
        self.sampleRateComboBox.currentIndexChanged.connect(self.onSampleRateChanged)
        layout.addWidget(self.sampleRateComboBox)

        self.message2 = QLabel("Buffer Size")
        layout.addWidget(self.message2)

        self.bufferSizeComboBox = QComboBox()
        self.bufferSizeComboBox.addItems([str(size) for size in self.BUFFER_SIZES])

        # Set current buffer size or indicate unknown
        current_buffer_size = self.read('quantum')
        if current_buffer_size == "Unknown":
            self.bufferSizeComboBox.addItem(current_buffer_size)
            self.bufferSizeComboBox.setCurrentIndex(self.bufferSizeComboBox.findText(current_buffer_size))
        else:
            current_buffer_size_index = self.bufferSizeComboBox.findText(current_buffer_size)
            if current_buffer_size_index >= 0:
                self.bufferSizeComboBox.setCurrentIndex(current_buffer_size_index)
        self.bufferSizeComboBox.currentIndexChanged.connect(self.onBufferSizeChanged)
        layout.addWidget(self.bufferSizeComboBox)

        self.setLayout(layout)

    def updateSampleRates(self):
        supported_rates = self.detectSupportedSampleRates()
        self.sampleRateComboBox.clear()
        self.sampleRateComboBox.addItems([str(rate) for rate in supported_rates])

    def detectSupportedSampleRates(self):
        return self.SAMPLE_RATES

    def onSampleRateChanged(self, index):
        rate = self.sampleRateComboBox.currentText()
        if rate.isdigit():
            self.change(rate, 'rate')
            unknown_index = self.sampleRateComboBox.findText("Unknown")
            if unknown_index >= 0:
                self.sampleRateComboBox.removeItem(unknown_index)

    def onBufferSizeChanged(self, index):
        size = self.bufferSizeComboBox.currentText()
        if size.isdigit():
            self.change(size, 'quantum')

            unknown_index = self.bufferSizeComboBox.findText("Unknown")
            if unknown_index >= 0:
                self.bufferSizeComboBox.removeItem(unknown_index)

    def read(self, prop):
        try:
            setting = subprocess.check_output(["pw-metadata", "-n", "settings", "0", f"clock.force-{prop}"])
            value = setting.decode("UTF-8").split("value:'")[1].split("' type:")[0]
            return value
        except subprocess.CalledProcessError:
            return "Unknown"

    def change(self, value, prop):
        try:
            subprocess.run(["pw-metadata", "-n", "settings", "0", f"clock.force-{prop}", str(value)], check=True)
        except subprocess.CalledProcessError:
            self.showErrorMessage(f"Failed to update {prop}")

    def showErrorMessage(self, message):
        QMessageBox.critical(self, "Update Failed", message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Application()
    ex.show()
    sys.exit(app.exec())
