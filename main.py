import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from windows.discover import DiscoverWindow
from windows.control import ControlWindow, ControlWindowMotorType, ControlWindowMotor
from windows.connecting import ConnectingWindow

discover_window = ConnectingWindow('192.168.2.27')
discover_window.connect('destroy', Gtk.main_quit)
discover_window.show_all()

Gtk.main()