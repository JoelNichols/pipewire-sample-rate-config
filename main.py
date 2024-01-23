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

        layout.addWidget(QLabel('Current Audio Interface'))
        layout.addWidget(QLabel(self.getCurrentAudioInterface()))

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

    def getCurrentAudioInterface(self):
        try:
            sinks = subprocess.check_output(["pactl", "list", "sinks"]).decode("utf-8")
            active_sink = None
            current_sink = None
            for line in sinks.split('\n'):
                if "State: RUNNING" in line and current_sink is not None:
                    active_sink = current_sink
                    break
                elif line.startswith("Sink #"):
                    current_sink = line.split('#')[1].strip()
            if active_sink is not None:
                sink_info = subprocess.check_output(["pactl", "list", "sinks"]).decode("utf-8")
                sink_section = False
                for line in sink_info.split('\n'):
                    if line.startswith(f"Sink #{active_sink}"):
                        sink_section = True
                    elif line.startswith("Sink #") and sink_section:
                        break
                    elif sink_section and line.strip().startswith("Name:"):
                        full_name = line.split(' ')[1].strip()
                        # Simplify the interface name
                        simplified_name = self.simplifyInterfaceName(full_name)
                        return simplified_name
            return "Unknown"
        except subprocess.CalledProcessError:
            return "Unknown"

    def simplifyInterfaceName(self, full_name):
        parts = full_name.replace('.', '_').split('_')

        relevant_parts = []
        for part in parts:
            if part.lower() in ["alsa", "usb", "output", "input", "sink", "source", "audio", "card", "device",
                                "multichannel", "00"]:
                continue
            # Exclude likely serial numbers or similar identifiers
            if any(char.isdigit() for char in part):
                continue
            relevant_parts.append(part)

        simplified_name = ' '.join(relevant_parts)

        # Return the simplified name, or a generic label if it's empty
        return simplified_name if simplified_name else "Audio Interface"

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
