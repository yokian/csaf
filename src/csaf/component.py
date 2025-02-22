""" Simple Pub/Sub Component

Ethan Lew
06/17/2020

component models a simple class that contains multiple subscribers/publishers to represent a component
"""

import time
import json
import threading

import zmq

# override root logger with csaf logger
from . import csaf_logger as logging


class Component:
    """ Represent a Pub/Sub Component

    Can have publishers and subscribers, with serialization/deserialization to encode/decode
    information.
    """
    @staticmethod
    def serialize(data_dict):
        """default component serialization implementation"""
        return str.encode(json.dumps(data_dict))

    @staticmethod
    def deserialize(data_string):
        """default component deserialization implementation"""
        return json.loads(data_string.decode())

    def __init__(self, num_inputs, num_outputs, name=None):
        # zeroMQ members
        self.zmq_context = None
        self.input_socks = None
        self.output_socks = None
        self._in_ports, self._out_ports = False, False

        # threads to manage subscribers over
        self.subscriber_threads = None
        self.stop_threads = None

        # pub/sub count parameters
        self._num_inputs = num_inputs
        self._num_outputs = num_outputs

        # debug flag
        self._debug = False
        self._n_publish = [0] * num_outputs
        self._n_subscribe = [0] * num_inputs

        self._name = "system" if name is None else name

    def debug_start(self):
        return f"Component '{self.name}' {self.__class__.__name__}"

    def print_if_debug(self, s):
        if self.debug_node:
            logging.debug(self.debug_start() + s)

    def init_net(self, in_ports, out_ports):
        """network context initialization"""
        self.stop_threads = threading.Event()

        if self.zmq_context is not None:
            self.unbind()

        self.zmq_context = zmq.Context()

        assert len(out_ports) == self.num_output_socks
        assert len(in_ports) == self.num_input_socks
        self._in_ports, self._out_ports = in_ports, out_ports

    def bind_output(self):
        """create component output ports"""
        assert self._out_ports is not False, f"No output ports specified! Make sure to call init_net first"

        # setup publishers over TCP network
        # TODO: uses TCP -- maybe make configurable for zeroMQ's various transport options
        self.output_socks = []
        for idx in range(self.num_output_socks):
            sock = self.zmq_context.socket(zmq.PUB)
            sock.bind(f"tcp://*:{self._out_ports[idx]}")
            self.output_socks.append(sock)

    def connect_input(self):
        """connect input ports to the component outputs"""
        assert self._in_ports is not False, f"no input ports specified! Make sure to call init_net first"

        # setup subscribers over TCP network
        self.input_socks = []
        self.input_topics = []
        for idx in range(self.num_input_socks):
            sock = self.zmq_context.socket(zmq.SUB)
            sock.connect(f"tcp://127.0.0.1:{self._in_ports[idx][0]}")
            topic = self._in_ports[idx][1]
            self.print_if_debug(f"binding socket {self._in_ports[idx][0]} with topic {topic}")
            sock.setsockopt_string(zmq.SUBSCRIBE, topic)
            sock.setsockopt(zmq.CONFLATE, 1)
            self.input_socks.append(sock)
            self.input_topics.append(topic)

        # TODO: needed for some reason -- better way to make sure subscribers are ready?
        time.sleep(0.2)


    def bind(self, in_ports, out_ports):
        """bind subscribers/publishers to their respective ports"""
        self.init_net()
        self.bind_output(out_ports)
        self.connect_input(in_ports)


    def unbind(self):
        """unbind from ports and destroy zmq context"""

        if self.stop_threads is not None:
            self.stop_threads.clear()

        def close_socks(socks):
            for sock in socks:
                sock.close()

        if self.input_socks is not None:
            close_socks(self.input_socks)

        if self.output_socks is not None:
            close_socks(self.output_socks)

        if self.zmq_context is not None:
            self.zmq_context.term()

    def send_message(self, output_idx, message, topic="unnamed"):
        """send a message over output number output_idx """
        if self.debug_node:
            logging.debug(f"Component '{self.name}' {self.__class__.__name__} Socket {output_idx} Sending "
                  f"{self._n_publish[output_idx]} Topic '{topic}'")
        if topic:
            self.output_socks[output_idx].send_string(topic, zmq.SNDMORE)
            self.output_socks[output_idx].send_pyobj(message)
        else:
            self.output_socks[output_idx].send(self.serialize(message))
        self._n_publish[output_idx] += 1

    def reset(self):
        raise NotImplementedError

    def send_output(self, overwrite_buffer):
        raise NotImplementedError

    @property
    def num_input_socks(self):
        return self._num_inputs

    @property
    def num_output_socks(self):
        return self._num_outputs

    @property
    def debug_node(self):
        return self._debug

    @debug_node.setter
    def debug_node(self, s):
        assert type(s) is bool, f"setting debug_node must be boolean type (got {type(s)})"
        self._debug = s
