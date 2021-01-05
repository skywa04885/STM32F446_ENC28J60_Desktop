import gi
import socket
import time
import enum
from struct import pack, unpack
from .control_packet import ControlPacketMotorType, ControlPacketMotorMode, ControlPacketOpcode, ControlPacketType, ControlPacketArgType

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

CONTROL_PORT = 7513

class ControlWindowMotor:
    def __init__ (self, type, id_, mode, min_sps, max_sps):
        self.type = type
        self.id_ = id_
        self.mode = mode
        self.min_sps = min_sps
        self.max_sps = max_sps

class ControlWindow(Gtk.Window):
    def __init__ (self, ip, motors):
        self.motor_pages = []
        self.title = f'Aansturing voor {ip}'
        self.ip = ip

        # Creates the GTK Window
        Gtk.Window.__init__(self, title = self.title)

        # Creates the UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        self.udp_socket.bind(('0.0.0.0', CONTROL_PORT))

        #
        # Creates the header
        #

        # Creates the HeaderBar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.props.title = self.title
        self.set_titlebar(self.header_bar)

        #
        # Prepares the motors
        #

        # Creates the notebook
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        # Creates the motors
        for m in motors:
            label = str(m.type).split('.')[1]

            # Creates the motor page box
            motor_page = Gtk.Box()
            motor_page.set_border_width(10)

            # Creates the VBOX
            vbox_motor_controls = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
            motor_page.add(vbox_motor_controls)

            # Checks the motor type, and adds the controls
            if m.type == ControlPacketMotorType.Stepper:
                # Creates the motor status
                hbox_motor_status = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                vbox_motor_controls.pack_start(hbox_motor_status, False, False, 6)

                motor_status_position_label = Gtk.Label('Positie: */*')
                hbox_motor_status.pack_start(motor_status_position_label, False, False, 12)

                motor_status_speed_label = Gtk.Label(f'Snelheid: */{m.min_sps}/{m.max_sps}')
                hbox_motor_status.pack_start(motor_status_speed_label, False, False, 12)

                motor_status_spinner = Gtk.Spinner()
                hbox_motor_status.pack_start(motor_status_spinner, False, False, 12)

                vbox_motor_controls.pack_start(Gtk.Separator(), False, False, 12)

                # Creates the position control
                hbox_motor_position_control = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                vbox_motor_controls.pack_start(hbox_motor_position_control, False, False, 0)

                moitor_position_control_label = Gtk.Label('Positie:')
                entry_position = Gtk.Entry()
                entry_position.connect('changed', self.on_text_change)

                button_move_to = Gtk.Button(label = 'Begin beweging')
                button_move_to.connect('pressed', self.on_button_move_pressed, m, entry_position)

                hbox_motor_position_control.pack_start(moitor_position_control_label, False, False, 6)
                hbox_motor_position_control.pack_start(entry_position, False, False, 6)
                hbox_motor_position_control.pack_start(button_move_to, False, False, 6)

                # Adds the disable and activate buttons ( Only if manual mode enabled )
                if m.type == ControlPacketMotorMode.Manual:
                    vbox_motor_controls.pack_start(Gtk.Separator(), False, False, 12)
                    hbox_motor_control = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                    vbox_motor_controls.pack_start(hbox_motor_control, False, False, 6)

                    motor_control_enable = Gtk.Button(label = 'Activeer')
                    hbox_motor_control.pack_start(motor_control_enable, False, False, 6)

                    motor_control_disable = Gtk.Button(label = 'Deactiveer')
                    hbox_motor_control.pack_start(motor_control_disable, False, False, 6)
            elif m.type == ControlPacketMotorType.Servo:
                pass
            elif m.type == ControlPacketMotorType.DC:
                pass

            # Adds the page to the GTK notebook
            self.notebook.append_page(motor_page, Gtk.Label(f'M{m.id_ + 1} ({label})'))
            self.motor_pages.append(motor_page)

    def on_text_change(self, widget):
        text = widget.get_text().strip()
        widget.set_text(''.join([i for i in text if i in '-0123456789']))
    
    def on_button_move_pressed(self, widget, m, entry):
        text = entry.get_text()

        # Builds the move packet
        data = pack('<BBIHHHBHHiHH',
            (ControlPacketType.Request.value | (ControlPacketOpcode.StepperMove.value << 1)), 0, 1, 0,
            ControlPacketArgType.U8.value, 1, m.id_,        # Motor ID
            ControlPacketArgType.I32.value, 4, int(text),   # Position,
            ControlPacketArgType.End.value, 1               # End
        )
        self.udp_socket.sendto(data, (self.ip, CONTROL_PORT))
