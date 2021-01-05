import gi
import socket
import time
from struct import * 

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

DISCOVER_PORT = 7512

DISCOVER_PREFIX = (0x67, 0x61, 0x79)

DISCOVER_OPCODE_REQUEST = 0
DISCOVER_OPCODE_RESPONSE = 1

class DiscoverWindowMCUElement(Gtk.ListBoxRow):
    def __init__ (self, ip, vstr):
        super(Gtk.ListBoxRow, self).__init__()

        self.ip = ip
        self.vstr = vstr

        self.add(Gtk.Label(label=f'{ip} -> {vstr}'))

class DiscoverWindow(Gtk.Window):
    title = 'Ontdek MCU\'s'

    def __init__ (self):
        self.listening_timeout = None
        self.io_watcher = None

        # Creates the GTK Window
        Gtk.Window.__init__(self, title = self.title)
        self.set_default_size(500, 400)
        
        #
        # Header
        #
        
        # Creates the HeaderBar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.props.title = self.title
        self.set_titlebar(self.header_bar)

        # Creates the HeaderBar HBOX
        self.header_bar_hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)

        # Creates the refresh button
        self.refresh_button = Gtk.Button(label = 'Refresh')
        self.refresh_button.connect('clicked', self.on_refresh_button_pressed)
        self.header_bar_hbox.pack_start(self.refresh_button, False, False, 6)

        # Creates the refresh spinner
        self.refresh_spinner = Gtk.Spinner()
        self.header_bar_hbox.pack_start(self.refresh_spinner, False, False, 6)

        # Assigns the header bar button box to the HeaderBar
        self.header_bar.pack_start(self.header_bar_hbox)

        #
        # Content
        #

        # Creates the list box
        self.mcu_list_box = Gtk.ListBox()
        self.mcu_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.add(self.mcu_list_box)

        #
        # Creates the UDP Server
        #

        # Creates the UDP broadcast socket
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.broadcast_socket.bind(('0.0.0.0', DISCOVER_PORT))
    
    def on_discover_packet(self, source, cbcond):
        # Reads the packet which is now available, and checks if it is not
        #  our broadcast one, if it is... Just ignore
        data, _, _, address = self.broadcast_socket.recvmsg(1024)
        if address[0] == socket.gethostbyname(socket.gethostname()):
            return True

        # Prints to the console that packet has been received
        print(f'{time.time()} MCU ontdekt op: {address[0]}:{address[1]}')

        # Parses the response packet
        _, _, _, _, vstrl = unpack('BBBBB', data[0:5]);
        vstr = (f'{vstrl}c', data[5:])

        # Adds the device to the device list
        self.mcu_list_box.insert(DiscoverWindowMCUElement(f'{address[0]}:{address[1]}', vstr[1].decode('utf-8')), 0)
        self.mcu_list_box.show_all()

        # Parses the packet
        return True

    def list_box_delete_row(self, widget):
        self.mcu_list_box.remove(widget)

    def on_refresh_button_pressed(self, widget):
        print(f'{time.time()} ontdekking gestart')

        self.refresh_spinner.start()
        self.mcu_list_box.foreach(self.list_box_delete_row)

        # Checks if there is an existing IO watcher, if so remove it
        #  and create a new one
        if self.io_watcher != None:
            GLib.source_remove(self.io_watcher)
        self.io_watcher = GLib.io_add_watch(self.broadcast_socket.fileno(), GLib.IO_IN, self.on_discover_packet)

        # Sends the broadcast packet
        pdata = pack('BBBBBs', DISCOVER_PREFIX[0], DISCOVER_PREFIX[1], DISCOVER_PREFIX[2], DISCOVER_OPCODE_REQUEST, 0, b'')
        self.broadcast_socket.sendto(pdata, ('255.255.255.255', DISCOVER_PORT))

        # Checks if an current event needs to be stopped, and create
        #  the new timed-out event, to finish seaching
        if self.listening_timeout != None:
            GLib.source_remove(self.listening_timeout)
        self.listening_timeout = GLib.timeout_add_seconds(5, self.on_disable_spinner)
    
    def on_disable_spinner(self):
        print(f'{time.time()} ontdekking gestopt')

        # Stops the spinner
        self.refresh_spinner.stop()

        # Removes the IO watcher
        if self.io_watcher != None:
            GLib.source_remove(self.io_watcher)
            self.io_watcher = None

        # Sets the listener timeout to none, since the event
        #  will not exist anymore
        self.listening_timeout = None
        return False
