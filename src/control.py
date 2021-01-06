import gi
import socket
import time
import enum
from struct import pack, unpack
from .control_packet import ControlPacketMotorType, ControlPacketMotorMode, ControlPacketOpcode, ControlPacketType, ControlPacketArgType, CONTROL_PREFIX, ControlPacketArgStepperStatus

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

CONTROL_PORT = 7588

class ControlWindowGTKStatus:
    def __init__ (self, pos, sps):
        self.pos = pos
        self.sps = sps
    
    def set_pos(self, cpos, tpos):
        self.pos.set_text(f'Positie: {cpos}->{tpos}')
    
    def set_sps(self, csps, mnsps, mxsps):
        self.sps.set_text(f'Speed {csps}/{mnsps}/{mxsps}')

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
        self.motor_status_gtk = []
        self.title = f'Aansturing voor {ip}'
        self.ip = ip
        self.motors = motors
        self.current_page = 0

        self.current_status_transmitter_glib = None
        self.io_watcher = None

        # Creates the GTK Window
        Gtk.Window.__init__(self, title = self.title)

        # Creates the UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        self.udp_socket.bind(('0.0.0.0', CONTROL_PORT))

        # Creates the packete listener
        self.io_watcher = GLib.io_add_watch(self.udp_socket.fileno(), GLib.IO_IN, self.on_socket_packet)
        
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
        self.notebook.connect('switch-page', self.on_switch_page)
        self.add(self.notebook)

        # Creates the motors
        for m in self.motors:
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

                self.motor_status_gtk.append(ControlWindowGTKStatus(motor_status_position_label, motor_status_speed_label))

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
                if m.mode == ControlPacketMotorMode.Manual:
                    vbox_motor_controls.pack_start(Gtk.Separator(), False, False, 12)
                    hbox_motor_control = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                    vbox_motor_controls.pack_start(hbox_motor_control, False, False, 6)

                    motor_control_enable = Gtk.Button(label = 'Activeer')
                    motor_control_enable.connect('pressed', self.on_stepper_enable_disable_pressed, m, True)
                    hbox_motor_control.pack_start(motor_control_enable, False, False, 6)

                    motor_control_disable = Gtk.Button(label = 'Deactiveer')
                    motor_control_disable.connect('pressed', self.on_stepper_enable_disable_pressed, m, False)
                    hbox_motor_control.pack_start(motor_control_disable, False, False, 6)
            elif m.type == ControlPacketMotorType.Servo:
                pass
            elif m.type == ControlPacketMotorType.DC:
                pass

            # Adds the page to the GTK notebook
            self.notebook.append_page(motor_page, Gtk.Label(f'M{m.id_ + 1} ({label})'))
            self.motor_pages.append(motor_page)

    def on_switch_page(self, notebook, page, page_num):
        self.current_page = page_num

        # Checks if there is an event registered, if so remove ut
        if self.current_status_transmitter_glib != None:
            GLib.source_remove(self.current_status_transmitter_glib)
            self.current_status_transmitter_glib = None

        # Gets the motor, and checks which event we need to register
        m = self.motors[page_num]
        if m.type == ControlPacketMotorType.Stepper:
            self.current_status_transmitter_glib = GLib.timeout_add(100, self.on_stepper_info_request_event)
        
        return True

    def on_stepper_info_request_event(self):
        print(f'{time.time()}: transmitting stepper info request')
        data = pack('<10sBBIHHHBHH',
            CONTROL_PREFIX,
            (ControlPacketType.Request.value | (ControlPacketOpcode.StepperStats.value << 1)), 0, 1, 0,
            ControlPacketArgType.U8.value, 1, self.current_page,        # Motor ID
            ControlPacketArgType.End.value, 1                           # End
        )
        self.udp_socket.sendto(data, (self.ip, CONTROL_PORT))
        return True

    def on_socket_packet(self, source, cbond):
        # Reads the data from the socket
        data, _, _, address = self.udp_socket.recvmsg(1024)

        # Unpacks the data, and chekcs if the current packet meets
        #  our requirements
        prefix, t_op, f, sn, tl = unpack('<10sBBIH', data[:18])
        if prefix != CONTROL_PREFIX:
            return True
        if (t_op & 1) != ControlPacketType.Reply.value:
            return True

        # Checks the response type, and parses the arguments
        op = (t_op & 0b01111111) >> 1
        if op == ControlPacketOpcode.StepperStats.value:
            start = 18
            while True:
                arg_type, arg_len = unpack('<HH', data[start:start + 4])

                # Checks the argument type, and parses it
                status = ControlPacketArgStepperStatus.parse(data[start + 4:start + 4 + arg_len])
                
                # Updates the status
                self.motor_status_gtk[status.id_].set_pos(status.cpos, status.tpos)
                self.motor_status_gtk[status.id_].set_sps(status.sps, self.motors[status.id_].min_sps, self.motors[status.id_].max_sps)
                break

        return True
    
    def on_text_change(self, widget):
        text = widget.get_text().strip()
        widget.set_text(''.join([i for i in text if i in '-0123456789']))

    def on_stepper_enable_disable_pressed(self, widget, m, ena):
        # Gets the opcode
        op = None
        if ena == True:
            op = ControlPacketOpcode.StepperEnable.value
        else:
            op = ControlPacketOpcode.StepperDisable.value

        # Builds and sends the packet
        data = pack('<10sBBIHHHBHH',
            CONTROL_PREFIX,
            (ControlPacketType.Request.value | (op << 1)), 0, 1, 0,
            ControlPacketArgType.U8.value, 1, m.id_,        # Motor ID
            ControlPacketArgType.End.value, 1               # End
        )
        self.udp_socket.sendto(data, (self.ip, CONTROL_PORT))
    
    def on_button_move_pressed(self, widget, m, entry):
        text = entry.get_text()
        data = pack('<10sBBIHHHBHHiHH',
            CONTROL_PREFIX,
            (ControlPacketType.Request.value | (ControlPacketOpcode.StepperMove.value << 1)), 0, 1, 0,
            ControlPacketArgType.U8.value, 1, m.id_,        # Motor ID
            ControlPacketArgType.I32.value, 4, int(text),   # Position,
            ControlPacketArgType.End.value, 1               # End
        )
        self.udp_socket.sendto(data, (self.ip, CONTROL_PORT))
