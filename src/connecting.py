import gi
import socket
import time
from struct import pack, unpack
from .control_packet import ControlPacketArgType, ControlPacketOpcode, ControlPacketType, CONTROL_PORT, ControlPacketMotorType, ControlPacketMotorMode
from .control import ControlWindowMotor, ControlWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

CONTROL_PORT = 7513

control_packet_motor_type_switcher = {
    0: ControlPacketMotorType.Stepper,
    1: ControlPacketMotorType.Stepper,
    2: ControlPacketMotorType.DC
}

cotnrol_packet_motor_mode_switcher = {
    0: ControlPacketMotorMode.Auto,
    1: ControlPacketMotorMode.Manual
}

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

        # Creates the packete listener
        self.io_watcher = GLib.io_add_watch(self.udp_socket.fileno(), GLib.IO_IN, self.on_udp_packet)

        # Starts connecting
        self.start_connecting()

    def on_udp_packet(self, source, cbond):
        # Reads the data from the socket
        data, _, _, address = self.udp_socket.recvmsg(1024)

        # Unpacks the data, and checks if the current packet
        #  meets our requirements
        t_op, f, sn, tl = unpack('<BBIH', data[:8])
        if (t_op & 1) != ControlPacketType.Reply.value or ((t_op & 0b01111111) >> 1) != ControlPacketOpcode.MotorInfo.value:
            return True

        # Loops over the arguments, and parses them
        motors = []
        start = 8
        while True:
            arg_type, arg_len = unpack('<HH', data[start:start + 4])

            # Checks the argument type, and parses it accordingly
            if arg_type == ControlPacketArgType.MotorStatus.value:
                id_, t, m, min_sps, max_sps = unpack('<BBBHH', data[start + 4:start + 4 + arg_len])
                motors.append(ControlWindowMotor(control_packet_motor_type_switcher.get(t), 
                    id_, cotnrol_packet_motor_mode_switcher.get(m), min_sps, max_sps))
            elif arg_type == ControlPacketArgType.End.value:
                break

            # Goes to the next argument
            start += 4 + arg_len

        # Closes the current window, and opens the control one
        control_window = ControlWindow(self.ip, motors)
        control_window.connect('destroy', Gtk.main_quit)
        control_window.show_all()

        self.udp_socket.close()
        self.destroy()
        
        return True

    def on_close_timeout(self):
        GLib.source_remove(self.io_watcher)

        self.progress_bar.set_text('Verbinding mislukt !')
        self.progress_bar.set_fraction(1.0)

        return False

    def start_connecting (self):
        # Updates the progress bar
        self.progress_bar.set_text(f'Verbinding wordt gemaakt met {self.ip}')
        self.progress_bar.set_fraction(0.1)

        # Sends the communication start packet
        data = pack('<BBIHs', (ControlPacketType.Request.value | (ControlPacketOpcode.MotorInfo.value << 1)), 0, 1, 0, b'')
        self.udp_socket.sendto(data, (self.ip, CONTROL_PORT))

        # Sets the timeout, which will close the window if response
        #  not in time
        self.close_timeout = GLib.timeout_add_seconds(3, self.on_close_timeout)


