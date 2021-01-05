import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.discover import DiscoverWindow
from src.control import ControlWindow
from src.connecting import ConnectingWindow

discover_window = DiscoverWindow()
discover_window.show_all()

Gtk.main()