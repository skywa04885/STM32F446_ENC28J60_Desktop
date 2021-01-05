import gi
import socket
import time
import enum

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

CONTROL_PORT = 7513

class ControlWindowMotorType(enum.Enum):
    Stepper = 1
    Servo = 2
    DC = 3

class ControlWindowMotor:
    def __init__ (self, type, id):
        self.type = type
        self.id = id

class ControlWindow(Gtk.Window):
    def __init__ (self, ip, motors):
        self.motor_pages = []
        self.title = f'Aansturing voor {ip}'
        self.ip = ip

        # Creates the GTK Window
        Gtk.Window.__init__(self, title = self.title)

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
            if m.type == ControlWindowMotorType.Stepper:
                # Creates the motor status
                hbox_motor_status = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                vbox_motor_controls.pack_start(hbox_motor_status, False, False, 6)

                motor_status_position_label = Gtk.Label('Positie: */*')
                hbox_motor_status.pack_start(motor_status_position_label, False, False, 12)

                motor_status_speed_label = Gtk.Label('Snelheid: */*')
                hbox_motor_status.pack_start(motor_status_speed_label, False, False, 12)

                motor_status_spinner = Gtk.Spinner()
                hbox_motor_status.pack_start(motor_status_spinner, False, False, 12)

                vbox_motor_controls.pack_start(Gtk.Separator(), False, False, 12)


                # Creates the position control
                hbox_motor_position_control = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                vbox_motor_controls.pack_start(hbox_motor_position_control, False, False, 0)

                moitor_position_control_label = Gtk.Label('Positie:')
                entry_position = Gtk.Entry()
                button_move_to = Gtk.Button(label = 'Begin beweging')

                hbox_motor_position_control.pack_start(moitor_position_control_label, False, False, 6)
                hbox_motor_position_control.pack_start(entry_position, False, False, 6)
                hbox_motor_position_control.pack_start(button_move_to, False, False, 6)

                vbox_motor_controls.pack_start(Gtk.Separator(), False, False, 12)

                # Creates the motor control
                hbox_motor_control = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
                vbox_motor_controls.pack_start(hbox_motor_control, False, False, 6)

                motor_control_enable = Gtk.Button(label = 'Activeer')
                hbox_motor_control.pack_start(motor_control_enable, False, False, 6)

                motor_control_disable = Gtk.Button(label = 'Deactiveer')
                hbox_motor_control.pack_start(motor_control_disable, False, False, 6)
            elif m.type == ControlWindowMotorType.Servo:
                pass
            elif m.type == ControlWindowMotorType.DC:
                pass

            # Adds the page to the GTK notebook
            self.notebook.append_page(motor_page, Gtk.Label(f'M{m.id} ({label})'))
            self.motor_pages.append(motor_page)
        
