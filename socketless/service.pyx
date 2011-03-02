# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

import logging

import cython

from collections import deque

from syncless import coio
from syncless.util import Queue

from socketless.channelserver import ChannelServer
from socketless.channel cimport Channel
from socketless.channel import DisconnectedException, Channel
from socketless.messenger cimport Messenger, Collector
from socketless.messenger import Messenger, Collector, invoke_all, send_all

from serialize cimport MessageReader
from serialize import MessageReader, MarshallerGenerator

class Method(object):
    """docstring for Method"""
    def __init__(self, signature, input, output):
        super(Method, self).__init__()
        self.signature = signature
        self.input_parameters = input
        self.output_parameters = output

class Protocol(object):
    """docstring for Protocol"""
    def __init__(self):
        super(Protocol, self).__init__()

cdef class Flusher:
    cdef object result_queues
    cdef object queue
    cdef Channel channel
    cdef object flush_task
    cdef object send_task

    def __init__(self, channel):
        self.channel = channel
        self.queue = Queue()
        self.result_queues = Queue()
        self.flush_task = coio.stackless.tasklet(self._flush)()
        self.send_task = coio.stackless.tasklet(self._send)()

    def _send(self):
        try:
            while True:
                result_queue = self.result_queues.popleft()
                result = result_queue.popleft()
                self.channel.send(result)
                if len(self.queue) == 0:
                    self.queue.append(True)
        except DisconnectedException:
            pass

    def _flush(self):
        try:
            while True:
                self.queue.popleft()
                self.channel.flush()
        except DisconnectedException:
            pass

    cdef expect(self, queue):
        self.result_queues.append(queue)

    cdef kill(self):
        self.flush_task.kill()

cdef class Service(object):
    cdef object marshaller_generator
    cdef object _protocol
    cdef dict implementations
    cdef dict bindings

    """docstring for Service"""
    def __init__(_self, _protocol, _marshaller_generator=MarshallerGenerator(), **implementations):
        super(Service, _self).__init__()
        _self.marshaller_generator = _marshaller_generator
        _self.protocol = _protocol
        _self.implementations = implementations
        _self.bindings = dict((method.signature, _self.create_binding(method, implementations[name])) for name, method in _self.protocol.methods.iteritems())

    def create_binding(self, method, implementation):
        marshal_input, unmarshal_input = self.marshaller_generator.compile(method.input_parameters)
        marshal_output, unmarshal_output = self.marshaller_generator.compile(method.output_parameters)

        if len(method.output_parameters) == 0:
            def wrap_callback(callback):
                def unmarshalling_callback_none():
                    callback('')
                return unmarshalling_callback_none
        elif len(method.output_parameters) == 1:
            def wrap_callback(callback):
                def unmarshalling_callback_single(result):
                    callback(marshal_output(result))
                return unmarshalling_callback_single
        else:
            def wrap_callback(callback):
                def unmarshalling_callback_tuple(result):
                    callback(marshal_output(*result))
                return unmarshalling_callback_tuple

        if len(method.input_parameters) == 0:
            def binding(callback, reader):
                implementation(wrap_callback(callback))
        elif len(method.input_parameters) == 1:
            def binding(callback, reader):
                implementation(wrap_callback(callback), unmarshal_input(reader))
        else:
            def binding(callback, reader):
                implementation(wrap_callback(callback), *unmarshal_input(reader))

        return binding

    cpdef _flush_loop(self, Channel channel, flush_queue):
        try:
            while True:
                flush_queue.popleft()
                channel.flush()
        except DisconnectedException:
            pass

    cpdef handle_connection(self, Channel channel):
        cdef MessageReader reader = MessageReader()
        cdef object flush_queue = Queue()
        cdef Flusher flusher = Flusher(channel)
        try:
            while True:
                queue = Queue()
                message = channel.recv()
                reader.update(message)
                signature = reader.read(1)
                binding = self.bindings[signature]
                flusher.expect(queue)
                binding(queue.append, reader)
        finally:
            flusher.kill()


class Server(object):
    """docstring for Server"""
    def __init__(self, listener, services):
        super(Server, self).__init__()
        self.services = dict((service.protocol.handshake[0], service) for service in services)
        self.listener = listener
        self.channel_server = ChannelServer(self.listener, handle_connection=self.handle_connection)

    def handshake(self, channel):
        logging.debug('Awaiting challenge.')
        challenge = channel.recv()
        logging.debug('Got challenge: "%s"', challenge)
        service = self.services.get(challenge, None)
        if not service:
            logging.warning('Failed handshake!')
            return None
        response = service.protocol.handshake[1]
        logging.debug('Correct challenge, sending response: "%s"', response)
        channel.send(response)
        channel.flush()
        logging.debug('Succesfully completed handshake.')
        return service

    def handle_connection(self, channel, addr):
        try:
            service = self.handshake(channel)
            if service:
                service.handle_connection(channel)
        except DisconnectedException:
            logging.debug('client %s disconnected', addr)
        except BaseException, e:
            logging.exception(e)
        finally:
            try:
                channel.close()
            except DisconnectedException, e:
                pass

    def serve(self):
        logging.debug("Listening on %s", self.listener)
        self.channel_server.serve()

    def stop(self):
        self.channel_server.stop()

class Client(object):
    """docstring for Client"""
    def __init__(self, listener, protocol, marshaller_generator=MarshallerGenerator(), tag=None):
        super(Client, self).__init__()
        self.tag = tag
        self.listener = listener
        self.protocol = protocol
        self.marshaller_generator = marshaller_generator
        self.messenger = Messenger(listener, handshake=self.protocol.handshake)
        self.wait_queue = Queue()
        self.async_wait_queue = Queue()
        self.async_replies = deque()
        for name, method in protocol.methods.iteritems():
            setattr(self, name, self._create_binding(method))
        for name, method in protocol.methods.iteritems():
            async_name = '%s_async' % name
            collector_name = '%s_collector' % name
            setattr(self, async_name, self._create_async_binding(method))
            setattr(self, collector_name, self._create_async_collector_binding(method))

    def _create_binding(self, method):
        marshal_input, unmarshal_input = self.marshaller_generator.compile(method.input_parameters)
        marshal_output, unmarshal_output = self.marshaller_generator.compile(method.output_parameters)
        signature = (method.signature, )
        wait_queue = self.wait_queue
        wait_queue_append = self.wait_queue.append
        wait_queue_pop = self.wait_queue.pop
        messenger_send = self.messenger.send
        def sync_callback(value, token):
            wait_queue_append(value)
        def sync_binding(*args):
            messenger_send(signature + marshal_input(*args), self, sync_callback)
            reply = wait_queue_pop()
            return None if reply is None else unmarshal_output(MessageReader(reply))
        return sync_binding


    def _create_async_collector_binding(self, method):
        marshal_output, unmarshal_output = self.marshaller_generator.compile(method.output_parameters)
        class AsyncCollector:
            __slots__ = ['_raw_collector']
            def __init__(self, count):
                self._raw_collector = Collector(count)
            def collect(self):
                data = self._raw_collector.collect()
                replies = [(None if value is None else unmarshal_output(MessageReader(value)), token) for value, token in data]
                return replies
        return AsyncCollector

    def _create_async_binding(self, method):
        marshal_input, unmarshal_input = self.marshaller_generator.compile(method.input_parameters)
        signature = (method.signature, )
        async_wait_queue_len = self.async_wait_queue.__len__
        async_wait_queue_append = self.async_wait_queue.append
        messenger_send = self.messenger.send
        async_replies_append = self.async_replies.append
        def async_binding(collector, *args):
            messenger_send(signature + marshal_input(*args), self, collector._raw_collector)
        return async_binding

    def is_connected(self):
        return self.messenger.connected if self.messenger else False

    def close(self):
        if self.messenger:
            self.messenger.close()
            self.messenger = None

cpdef send_all_clients(message, clients, collector):
    for client in clients:
        (<Messenger>(client.messenger)).send(message, client, collector)

class MulticastClient:
    """docstring for MulticastClient"""
    def __init__(self, protocol, marshaller_generator=MarshallerGenerator()):
        self.protocol = protocol
        self.marshaller_generator = marshaller_generator
        for name, method in protocol.methods.iteritems():
            setattr(self, name, self._create_binding(method))
        for name, method in protocol.methods.iteritems():
            setattr(self, '%s_async' % name, self._create_async_binding(method))
            setattr(self, '%s_collector' % name, self._create_async_collector_binding(method))

    def _create_binding(self, method):
        marshal_input, unmarshal_input = self.marshaller_generator.compile(method.input_parameters)
        marshal_output, unmarshal_output = self.marshaller_generator.compile(method.output_parameters)
        signature = method.signature
        def multi_binding(clients, *args):
            replies = invoke_all((signature,) + marshal_input(*args), [(client, client.messenger) for client in clients])
            return [(client, None if reply is None else unmarshal_output(MessageReader(reply))) for reply, client in replies]
        return multi_binding

    def _create_async_collector_binding(self, method):
        marshal_output, unmarshal_output = self.marshaller_generator.compile(method.output_parameters)
        class MultiAsyncCollector:
            __slots__ = ['_raw_collector', 'clients']
            def __init__(_self, clients, count):
                _self.clients = clients
                _self._raw_collector = Collector(count * len(_self.clients))
            def collect(_self):
                replies = dict()
                replies_setdefault = replies.setdefault
                data = _self._raw_collector.collect()
                for value, token in data:
                    replies_setdefault(token, []).append(unmarshal_output(MessageReader(value)))
                return replies
        return MultiAsyncCollector

    def _create_async_binding(self, method):
        marshal_input, unmarshal_input = self.marshaller_generator.compile(method.input_parameters)
        signature = method.signature
        def async_multi_binding(collector, *args):
            send_all_clients((signature,) + marshal_input(*args), collector.clients, collector._raw_collector)
        return async_multi_binding
