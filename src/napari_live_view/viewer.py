import json
import os
from qtpy.QtWidgets import QPushButton, QWidget, QLabel, QLineEdit, QGridLayout, QSizePolicy, QVBoxLayout
from .receiver import Receiver

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import napari

class Viewer(QWidget):
    """"Viewer class.
    
    This class connects the Receiver to napari layers, and adds dock widgets.
    """

    def __init__(self, viewer: 'napari.viewer.Viewer'):
        super().__init__()
        """Initialise Viewer class."""       

        self.viewer = viewer
        self.receiver = Receiver()

        self.layout = QVBoxLayout()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setLayout(self.layout)

        self.frames_shown = 0

        self.add_connections_widget()
        self.add_counter_widget()
        self.get_defaults()
        
    def get_defaults(self):
        """Gets default endpoint from config file. 
        
        Creates default file if it doesn't already exist.
        """
        home = os.environ['HOME']
        path = home + "/.config/napari/live_view_default.json"

        while not os.access(path, os.F_OK):
            print("Defaults file created") 
            with open(os.path.join((home + "/.config/napari"), "live_view_default.json"), 'w') as f:
                defaults = {
                    "default_endpoint": ""
                }
                json.dump(defaults, f)

        with open(path) as f:
            default = json.load(f)
            endpoint = default["default_endpoint"]
            if endpoint != "": # better way to do this? - additional field T/F if a defaults being used?
                self.endpoint_input.insert(endpoint)
                self.button_clicked()

    def hideEvent(self, event):
        """Overwrites QWidget event to close ZMQ connection when widget is hidden."""
        self.disconnect()

    def update_layer(self, img):
        """Updates or adds layer in napari with given image."""
        if img is not None:
            try:
                self.viewer.layers['result'].data = img
            except KeyError:
                    self.viewer.add_image(
                        img, name='result'
                    )
            self.frames_shown += 1
            self.update_counters()

    def update_counters(self):
        """Repaints frames shown and received counters in dock widget."""
        self.frames_shown_counter.setText(str(self.frames_shown))
        self.frames_shown_counter.repaint()
        self.frames_recvd_counter.setText(str(self.receiver.frames_received))
        self.frames_recvd_counter.repaint()

    def reset_counters(self):
        """Resets frames shown and received counters to zero and updates widget
        display.
        """
        self.frames_shown = 0
        self.receiver.frames_received = 0
        self.update_counters()

    def add_connections_widget(self):
        """Adds endpoint URL text input and connect button widgets."""
        connections = GridWidget()
        self.layout.addWidget(connections)

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("Endpoint URL")
        self.connect_button = QPushButton("CONNECT")
        self.connect_button.clicked.connect(self.button_clicked)

        connections.add(self.endpoint_input, 1, 1)
        connections.add(self.connect_button, 2, 1)

    def add_counter_widget(self):
        """Adds counter widgets with labels, and reset button."""
        counter = GridWidget()
        self.layout.addWidget(counter)

        frames_shown_label = QLabel("Frames shown: ")
        frames_recvd_label = QLabel("Frames received: ")

        self.frames_shown_counter = QLabel(str(self.frames_shown))
        self.frames_recvd_counter = QLabel(str(self.receiver.frames_received))
        reset_button = QPushButton("Reset counters")
        reset_button.clicked.connect(self.reset_counters)

        counter.add(self.frames_shown_counter, 1, 2)
        counter.add(frames_shown_label, 1, 1)
        counter.add(self.frames_recvd_counter, 2, 2)
        counter.add(frames_recvd_label, 2, 1)
        counter.add(reset_button, 3, 1, 1, 2)

    def button_clicked(self):
        """Called when the connections button is clicked.
        
        Depending on buttons state, calls either connect or disconnect, and
        updates appearance.
        """
        if self.connect_button.text() == "CONNECT":
            self.connect_button.setText("DISCONNECT")
            self.endpoint_input.setReadOnly(True) 
            # could have the input detect if text is changed and automatically disconnect and reconnect?
            self.endpoint_url = self.endpoint_input.text()
            self.connect(self.endpoint_url)
        else:
            self.connect_button.setText("CONNECT")
            self.endpoint_input.setReadOnly(False)
            self.disconnect()

    def connect(self, endpoint_url):
        """Connects given endpoint URL to receiver, starts and connects worker."""
        self.receiver.connect(endpoint_url)
        self.receiver.start_worker()
        self.receiver.connect_worker(self.update_layer)
        if self.receiver.connected:
            print("Connected") # move to receiver?

    def disconnect(self):
        """Stops worker."""
        if self.receiver.connected:
            self.receiver.stop_worker()

class GridWidget(QWidget):
    """GridWidget class.
    
    This class inherits from QWidget and creates a grid layout."""
    def __init__(self):
        super().__init__()
        """Initialise GridWidget class."""

        self.layout = QGridLayout()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setLayout(self.layout)

    def add(self, widget, row, col, rowspan=1, colspan=1):
        """Adds given widget to the grid at row/col given."""
        self.layout.addWidget(widget, row, col, rowspan, colspan)