import zmq
import time
import numpy as np
from napari.qt.threading import thread_worker

class Receiver():
    """Receiver class.
    
    This class controls the napari thread worker that receives and formats
    data from ZMQ.
    """

    def __init__(self):
        """Initialise receiver class."""
        self.endpoint_url = ""
        self.frames_received = 0
        self.connected = False

    def connect(self, endpoint_url):
        """Creates ZMQ context and socket, connects to endpoint URL given."""
        try:
            self.endpoint_url = endpoint_url
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.socket.connect(self.endpoint_url)
            self.connected = True
        except:
            print("Invalid url")
    
    def disconnect(self):
        """Disconnects from ZMQ socket and destroys context."""
        self.connected = False
        self.socket.disconnect(self.endpoint_url)
        self.context.destroy()
        

    def start_worker(self):
        """Creates worker from @thread_worker decorated function, starts worker."""
        self.worker = self.yield_frames()
        self.worker.start()

    def connect_worker(self, func):
        """Connects worker to given function."""
        self.worker.yielded.connect(func)

    # combine start_worker and connect_worker?

    def stop_worker(self):
        """Stops thread worker and waits until aborted to call disconnect."""
        self.worker.quit()
        aborted = False
        while not aborted:
            if self.worker.aborted:
                self.disconnect()
                aborted = True
                print("Disconnected")

    @thread_worker
    def yield_frames(self):
        """Receives data from socket.
        
        @thread_worker decorated function.
        """
        while self.connected:

            header = {}
            frame_data = None
            buf = None

            flags = self.socket.getsockopt(zmq.EVENTS)
            # Get socket event flags

            # Keep handling socket events until all flags are cleared
            while flags != 0:
                
                if flags & zmq.POLLIN:

                    # Receive frame header
                    header = self.socket.recv_json()

                    # Receive data payload
                    msg = self.socket.recv()
                    buf = memoryview(msg)

                    # Increment frames received counter
                    self.frames_received += 1

                flags = self.socket.getsockopt(zmq.EVENTS) 

            # Convert last received payload into numpy array and reshape
            if buf is not None:
                array = np.frombuffer(buf, dtype=header['dtype'])
                frame_data = array.reshape([int(header["shape"][0]), int(header["shape"][1])])

            yield frame_data
            
            time.sleep(0.1)