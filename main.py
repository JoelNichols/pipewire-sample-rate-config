#!/usr/bin/env python

import sys
import subprocess
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

class Application(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.SAMPLE_RATES = (44100, 48000, 88200, 96000)
        self.BUFFER_SIZES = (32, 64, 128, 256, 512, 1024)

        self.set_title("Pipewire Sample Rate Settings")
        self.set_default_size(350, 200)

        self.init_ui()

    def init_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.set_child(vbox)

        message = Gtk.Label(label="Sample Rate")
        vbox.append(message)

        self.sample_rate_combo_box = Gtk.ComboBoxText()
        self.update_sample_rates()
        vbox.append(self.sample_rate_combo_box)

        message2 = Gtk.Label(label="Buffer Size")
        vbox.append(message2)

        self.buffer_size_combo_box = Gtk.ComboBoxText()
        self.update_buffer_sizes()
        vbox.append(self.buffer_size_combo_box)

    def update_sample_rates(self):
        supported_rates = self.detect_supported_sample_rates()
        self.sample_rate_combo_box.append_text("Default")
        for rate in supported_rates:
            self.sample_rate_combo_box.append_text(str(rate))

        current_rate = self.read("rate")
        index = self.get_index_in_combo(self.sample_rate_combo_box, current_rate)
        if index == -1 and current_rate.isdigit() and current_rate != "0":
            self.sample_rate_combo_box.append_text(current_rate)
            index = self.get_index_in_combo(self.sample_rate_combo_box, current_rate)
        self.sample_rate_combo_box.set_active(index)
        self.sample_rate_combo_box.connect("changed", self.on_sample_rate_changed)

    def update_buffer_sizes(self):
        for size in self.BUFFER_SIZES:
            self.buffer_size_combo_box.append_text(str(size))

        current_buffer_size = self.read("quantum")
        # Fallback to the first size if the current size is invalid or not set
        if current_buffer_size == "0" or not current_buffer_size.isdigit():
            current_buffer_size = str(self.BUFFER_SIZES[0])  # Choose a sensible fallback
        index = self.get_index_in_combo(self.buffer_size_combo_box, current_buffer_size)
        if index == -1:
            self.buffer_size_combo_box.append_text(current_buffer_size)
            index = self.get_index_in_combo(self.buffer_size_combo_box, current_buffer_size)
        self.buffer_size_combo_box.set_active(index)
        self.buffer_size_combo_box.connect("changed", self.on_buffer_size_changed)

    def detect_supported_sample_rates(self):
        return self.SAMPLE_RATES

    def on_sample_rate_changed(self, combo):
        rate = combo.get_active_text()
        if rate == "Default":
            self.remove_setting("rate")
        elif rate.isdigit():
            self.change(rate, "rate")

    def on_buffer_size_changed(self, combo):
        size = combo.get_active_text()
        if size.isdigit():
            self.change(size, "quantum")

    def read(self, prop):
        try:
            setting = subprocess.check_output(["pw-metadata", "-n", "settings", "0", f"clock.force-{prop}"])
            value = setting.decode("UTF-8").split("value:'")[1].split("' type:")[0]
            if value == "0":  # If the value is 0, treat it as an invalid setting
                return "Default" if prop == "rate" else str(self.BUFFER_SIZES[0])
            return value
        except subprocess.CalledProcessError:
            return "Default" if prop == "rate" else str(self.BUFFER_SIZES[0])

    def change(self, value, prop):
        try:
            subprocess.run(["pw-metadata", "-n", "settings", "0", f"clock.force-{prop}", str(value)], check=True)
        except subprocess.CalledProcessError:
            self.show_error_message(f"Failed to update {prop}")

    def remove_setting(self, prop):
        try:
            subprocess.run(["pw-metadata", "-n", "settings", "-r", "0", f"clock.force-{prop}"], check=True)
        except subprocess.CalledProcessError:
            self.show_error_message(f"Failed to remove {prop} setting")

    def show_error_message(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Update Failed",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def get_index_in_combo(self, combo, text):
        model = combo.get_model()
        for i, row in enumerate(model):
            if row[0] == text:
                return i
        return -1

def on_activate(app):
    win = Application()
    app.add_window(win)
    win.show()

if __name__ == '__main__':
    app = Gtk.Application(application_id="com.example.PipewireSettings")
    app.connect("activate", on_activate)
    app.run(sys.argv)
