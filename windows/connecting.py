import gi
import socket
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

CONTROL_PORT = 7512

class ConnectingWindow(Gtk.Window):
    def __init__ (self, ip):
        self.ip = ip
        self.title = 'Even gedult a.u.b.'

        # Creates the GTK Window
        Gtk.Window.__init__(self, title = self.title)
        self.set_default_size(300, 60)
        self.set_resizable(False)

        # Creates the VBOX
        self.vbox_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        self.add(self.vbox_main)

        # Creates the loader
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text('...')
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_margin_left(12)
        self.progress_bar.set_margin_right(12)
        self.vbox_main.pack_end(self.progress_bar, True, True, 12)

        # Creates the UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        self.udp_socket.bind(('0.0.0.0', CONTROL_PORT))

        # Starts connecting
        self.start_connecting()

    def start_connecting (self):
        # Updates the progress bar
        self.progress_bar.set_text(f'Verbinding wordt gemaakt met {self.ip}')
        self.progress_bar.set_fraction(0.1)

        # Sends the communication start packet
