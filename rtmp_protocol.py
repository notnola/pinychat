"""
Provides classes for creating RTMP (Real Time Message Protocol) servers and
clients.
"""

# SUPER DEBUGGERY EDITION

# SUPER_DEBUGGERY = False # :D

# def superDebug(k, value):
#     if SUPER_DEBUGGERY: print("SUPER DEBUGGERY [" + str(k) + "] " + str(value))
#
# def superDebugNotice(notice):
#     if SUPER_DEBUGGERY: print("SUPER DEBUGGERY -- " + notice + " --")
#
# def superDebugFooter():
#     if SUPER_DEBUGGERY: print("SUPER DEBUGGERY --")

import pyamf.amf0
import pyamf.util.pure
import rtmp_protocol_base
import socket
import logging


class FileDataTypeMixIn(pyamf.util.pure.DataTypeMixIn):
    """
    Provides a wrapper for a file object that enables reading and writing of raw
    data types for the file.
    """

    def __init__(self, fileobject):
        self.fileobject = fileobject
        pyamf.util.pure.DataTypeMixIn.__init__(self)

    def read(self, length):
        return self.fileobject.read(length)

    def write(self, data):
        self.fileobject.write(data)

    def flush(self):
        self.fileobject.flush()

    def at_eof(self):
        return False


class DataTypes:
    """ Represents an enumeration of the RTMP message datatypes. """
    NONE = -1
    SET_CHUNK_SIZE = 1
    USER_CONTROL = 4
    WINDOW_ACK_SIZE = 5
    SET_PEER_BANDWIDTH = 6
    SHARED_OBJECT = 19
    COMMAND = 20


class SOEventTypes:
    """ Represents an enumeration of the shared object event types. """
    USE = 1
    RELEASE = 2
    CHANGE = 4
    MESSAGE = 6
    CLEAR = 8
    DELETE = 9
    USE_SUCCESS = 11


class UserControlTypes:
    """ Represents an enumeration of the user control event types. """
    STREAM_BEGIN = 0
    STREAM_EOF = 1
    STREAM_DRY = 2
    SET_BUFFER_LENGTH = 3
    STREAM_IS_RECORDED = 4
    PING_REQUEST = 6
    PING_RESPONSE = 7


class RtmpReader:
    """ This class reads RTMP messages from a stream. """

    chunk_size = 128

    def __init__(self, stream):
        """
        Initialize the RTMP reader and set it to read from the specified stream.
        """
        self.stream = stream

    def __iter__(self):
        return self

    def next(self):
        """ Read one RTMP message from the stream and return it. """
        if self.stream.at_eof():
            raise StopIteration

        # superDebugNotice("rtmp reader, reading incoming rtmp message from stream")

        # Read the message into body_stream. The message may span a number of
        # chunks (each one with its own header).
        message_body = []
        msg_body_len = 0
        header = rtmp_protocol_base.header_decode(self.stream)

        # FIXME: this should be really implemented inside header_decode
        if header.datatype == DataTypes.NONE:
            header = self.prv_header
        self.prv_header = header

        # superDebug("header", header)

        while True:
            read_bytes = min(header.bodyLength - msg_body_len, self.chunk_size)
            # superDebug("read_bytes", read_bytes)

            message_body.append(self.stream.read(read_bytes))
            msg_body_len += read_bytes
            if msg_body_len >= header.bodyLength:
                break
            next_header = rtmp_protocol_base.header_decode(self.stream)
            # superDebug("next_header", next_header)
            # WORKAROUND: even though the RTMP specification states that the
            # extended timestamp field DOES NOT follow type 3 chunks, it seems
            # that Flash player 10.1.85.3 and Flash Media Server 3.0.2.217 send
            # and expect this field here.
            # superDebug("header.timestamp", header.timestamp)
            # superDebug("header.timestamp >= 0x00ffffff", header.timestamp >= 0x00ffffff)
            if header.timestamp >= 0x00ffffff:
                self.stream.read_ulong()
            assert next_header.streamId == -1, (header, next_header)
            assert next_header.datatype == -1, (header, next_header)
            assert next_header.timestamp == -1, (header, next_header)
            assert next_header.bodyLength == -1, (header, next_header)
        assert header.bodyLength == msg_body_len, (header, msg_body_len)
        body_stream = pyamf.util.BufferedByteStream(''.join(message_body))

        # superDebug("body_stream_contents", ''.join(message_body))
        # superDebug("message_body", message_body)
        # superDebug("msg_body_len", msg_body_len)

        # Decode the message based on the datatype present in the header
        ret = {'msg':header.datatype}
        # superDebug("ret", ret)

        if ret['msg'] == DataTypes.USER_CONTROL:
            # superDebug("header.datatype enum", "USER_CONTROL")
            ret['event_type'] = body_stream.read_ushort()
            ret['event_data'] = body_stream.read()

            # superDebug("event_type", ret['event_type'])
            # superDebug("event_data", ret['event_data'])
        elif ret['msg'] == DataTypes.WINDOW_ACK_SIZE:
            # superDebug("header.datatype enum", "WINDOW_ACK_SIZE")
            ret['window_ack_size'] = body_stream.read_ulong()
            # superDebug("window_ack_size", ret['window_ack_size'])

        elif ret['msg'] == DataTypes.SET_PEER_BANDWIDTH:
            # superDebug("header.datatype enum", "SET_PEER_BANDWIDTH")

            ret['window_ack_size'] = body_stream.read_ulong()
            ret['limit_type'] = body_stream.read_uchar()

            # superDebug("window_ack_size", ret['window_ack_size'])
            # superDebug("limit_type", ret['limit_type'])

        elif ret['msg'] == DataTypes.SHARED_OBJECT:
            # superDebug("header.datatype enum", "SHARED_OBJECT")

            decoder = pyamf.amf0.Decoder(body_stream)
            obj_name = decoder.readString()
            curr_version = body_stream.read_ulong()
            flags = body_stream.read(8)

            # A shared object message may contain a number of events.
            events = []
            while not body_stream.at_eof():
                event = self.read_shared_object_event(body_stream, decoder)
                events.append(event)

            ret['obj_name'] = obj_name
            ret['curr_version'] = curr_version
            ret['flags'] = flags
            ret['events'] = events

            # superDebug("obj_name", ret['obj_name'])
            # superDebug("curr_version", ret['curr_version'])
            # superDebug("flags", ret['flags'])
            # superDebug("events", ret['events'])

        elif ret['msg'] == DataTypes.COMMAND:
            # superDebug("header.datatype enum", "COMMAND")
            decoder = pyamf.amf0.Decoder(body_stream)
            commands = []
            while not body_stream.at_eof():
                commands.append(decoder.readElement())
            ret['command'] = commands

        # elif ret['msg'] == DataTypes.NONE:
        #     print 'WARNING: message with no datatype received.', header
        #     return self.next()
            # superDebug("command", ret['command'])

        elif ret['msg'] == DataTypes.SET_CHUNK_SIZE:
            # superDebug("header.datatype enum", "SET_CHUNK_SIZE")
            ret['chunk_size'] = body_stream.read_ulong()
            # superDebug("chunk_size", ret['chunk_size'])
        else:
            assert False, header

        # superDebugFooter()

        logging.debug('recv %r', ret)
        return ret

    def read_shared_object_event(self, body_stream, decoder):
        """
        Helper method that reads one shared object event found inside a shared
        object RTMP message.
        """
        so_body_type = body_stream.read_uchar()
        so_body_size = body_stream.read_ulong()

        event = {'type':so_body_type}
        if event['type'] == SOEventTypes.USE:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.RELEASE:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.CHANGE:
            start_pos = body_stream.tell()
            changes = {}
            while body_stream.tell() < start_pos + so_body_size:
                attrib_name = decoder.readString()
                attrib_value = decoder.readElement()
                assert attrib_name not in changes, (attrib_name,changes.keys())
                changes[attrib_name] = attrib_value
            assert body_stream.tell() == start_pos + so_body_size,\
                (body_stream.tell(),start_pos,so_body_size)
            event['data'] = changes
        elif event['type'] == SOEventTypes.MESSAGE:
            start_pos = body_stream.tell()
            msg_params = []
            while body_stream.tell() < start_pos + so_body_size:
                msg_params.append(decoder.readElement())
            assert body_stream.tell() == start_pos + so_body_size,\
                (body_stream.tell(),start_pos,so_body_size)
            event['data'] = msg_params
        elif event['type'] == SOEventTypes.CLEAR:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        elif event['type'] == SOEventTypes.DELETE:
            event['data'] = decoder.readString()
        elif event['type'] == SOEventTypes.USE_SUCCESS:
            assert so_body_size == 0, so_body_size
            event['data'] = ''
        else:
            assert False, event['type']

        return event


class RtmpWriter:
    """ This class writes RTMP messages into a stream. """

    chunk_size = 128

    def __init__(self, stream):
        """
        Initialize the RTMP writer and set it to write into the specified
        stream.
        """
        self.stream = stream

    def flush(self):
        """ Flush the underlying stream. """
        self.stream.flush()

    def write(self, message):
        logging.debug('send %r', message)
        """ Encode and write the specified message into the stream. """
        datatype = message['msg']
        body_stream = pyamf.util.BufferedByteStream()
        encoder = pyamf.amf0.Encoder(body_stream)

        # superDebugNotice("rtmp writer, sending message into stream")
        # superDebug("message", message)
        # superDebug("datatype", datatype)

        if datatype == DataTypes.USER_CONTROL:
            # superDebug("enum", "USER_CONTROL")
            # superDebug("event_type", message['event_type'])
            # superDebug("event_data", message['event_data'])
            #
            body_stream.write_ushort(message['event_type'])
            body_stream.write(message['event_data'])
        elif datatype == DataTypes.WINDOW_ACK_SIZE:
            # superDebug("enum", "WINDOW_ACK_SIZE")
            # superDebug("window_ack_size", message['window_ack_size'])
            #
            body_stream.write_ulong(message['window_ack_size'])

        elif datatype == DataTypes.SET_PEER_BANDWIDTH:
            # superDebug("enum", "SET_PEER_BANDWIDTH")
            # superDebug("window_ack_size", message['window_ack_size'])
            # superDebug("limit_type", message['limit_type'])

            body_stream.write_ulong(message['window_ack_size'])
            body_stream.write_uchar(message['limit_type'])

        elif datatype == DataTypes.COMMAND:
            # superDebug("enum", "COMMAND")

            for command in message['command']:
                # superDebug("command iteration", command)
                encoder.writeElement(command)
        elif datatype == DataTypes.SHARED_OBJECT:
            # superDebug("enum", "SHARED_OBJECT")
            # superDebug("obj_name", message['obj_name'])
            # superDebug("curr_version", message['curr_version'])
            # superDebug("flags", message['flags'])

            encoder.serialiseString(message['obj_name'])
            body_stream.write_ulong(message['curr_version'])
            body_stream.write(message['flags'])

            for event in message['events']:
                # superDebug("event iteration", event)
                self.write_shared_object_event(event, body_stream)
        else:
            assert False, message

        self.send_msg(datatype, body_stream.getvalue())

        # superDebugFooter()

    def writepublish(self, message):
        # logging.debug('send %r', message)
        datatype = message['msg']
        body_stream = pyamf.util.BufferedByteStream()
        encoder = pyamf.amf0.Encoder(body_stream)

        # superDebugNotice("rtmp writer, sending message into stream")
        # superDebug("message", message)
        # superDebug("datatype", datatype)

        if datatype == DataTypes.USER_CONTROL:
            # superDebug("enum", "USER_CONTROL")
            # superDebug("event_type", message['event_type'])
            # superDebug("event_data", message['event_data'])

            body_stream.write_ushort(message['event_type'])
            body_stream.write(message['event_data'])

        elif datatype == DataTypes.WINDOW_ACK_SIZE:
            # superDebug("enum", "WINDOW_ACK_SIZE")
            # superDebug("window_ack_size", message['window_ack_size'])

            body_stream.write_ulong(message['window_ack_size'])
        elif datatype == DataTypes.SET_PEER_BANDWIDTH:
            # superDebug("enum", "SET_PEER_BANDWIDTH")
            # superDebug("window_ack_size", message['window_ack_size'])
            # superDebug("limit_type", message['limit_type'])

            body_stream.write_ulong(message['window_ack_size'])
            body_stream.write_uchar(message['limit_type'])

        elif datatype == DataTypes.COMMAND:
            # superDebug("enum", "COMMAND")

            for command in message['command']:
                # superDebug("command iteration", command)
                encoder.writeElement(command)

        elif datatype == DataTypes.SHARED_OBJECT:
            # superDebug("enum", "SHARED_OBJECT")
            # superDebug("obj_name", message['obj_name'])
            # superDebug("curr_version", message['curr_version'])
            # superDebug("flags", message['flags'])

            encoder.serialiseString(message['obj_name'])
            body_stream.write_ulong(message['curr_version'])
            body_stream.write(message['flags'])

            for event in message['events']:
                # superDebug("event iteration", event)
                self.write_shared_object_event(event, body_stream)
        else:
            assert False, message

        self.send_msg_publish(datatype, body_stream.getvalue())

        # superDebugFooter()

    def write_shared_object_event(self, event, body_stream):
        inner_stream = pyamf.util.BufferedByteStream()
        encoder = pyamf.amf0.Encoder(inner_stream)

        event_type = event['type']
        if event_type == SOEventTypes.USE:
            assert event['data'] == '', event['data']
        elif event_type == SOEventTypes.CHANGE:
            for attrib_name in event['data']:
                attrib_value = event['data'][attrib_name]
                encoder.serialiseString(attrib_name)
                encoder.writeElement(attrib_value)
        elif event['type'] == SOEventTypes.CLEAR:
            assert event['data'] == '', event['data']
        elif event['type'] == SOEventTypes.USE_SUCCESS:
            assert event['data'] == '', event['data']
        else:
            assert False, event

        body_stream.write_uchar(event_type)
        body_stream.write_ulong(len(inner_stream))
        body_stream.write(inner_stream.getvalue())

    def send_msg(self, datatype, body):
        """
        Helper method that send the specified message into the stream. Takes
        care to prepend the necessary headers and split the message into
        appropriately sized chunks.
        """

        # superDebugNotice("rtmp writer, send_msg")
        # superDebug("datatype", datatype)
        # superDebug("body", body)

        # Values that just work. :-)
        if 7 >= datatype >= 1:
            channel_id = 2
            stream_id = 0
        else:
            channel_id = 3
            stream_id = 0
        timestamp = 0

        header = rtmp_protocol_base.Header(
            channelId=channel_id,
            streamId=stream_id,
            datatype=datatype,
            bodyLength=len(body),
            timestamp=timestamp)
        rtmp_protocol_base.header_encode(self.stream, header)

        # superDebug("header", header)

        for i in xrange(0,len(body),self.chunk_size):
            chunk = body[i:i+self.chunk_size]
            self.stream.write(chunk)
            if i+self.chunk_size < len(body):
                rtmp_protocol_base.header_encode(self.stream, header, header)

    def send_msg_publish(self, datatype, body):
        """
        Helper method that send the specified message into the stream. Takes
        care to prepend the necessary headers and split the message into
        appropriately sized chunks.
        """

        # superDebugNotice("rtmp writer, send_msg")
        # superDebug("datatype", datatype)
        # superDebug("body", body)

        # Values that just work. :-)
        if 7 >= datatype >= 1:
            channel_id = 2
            stream_id = 1
        else:
            channel_id = 3
            stream_id = 1
        timestamp = 0

        header = rtmp_protocol_base.Header(
            channelId=11,
            streamId=1,
            datatype=datatype,
            bodyLength=len(body),
            timestamp=timestamp)
        rtmp_protocol_base.header_encode(self.stream, header)

        # superDebug("header", header)

        for i in xrange(0, len(body), self.chunk_size):
            chunk = body[i:i+self.chunk_size]
            self.stream.write(chunk)
            if i+self.chunk_size < len(body):
                rtmp_protocol_base.header_encode(self.stream, header, header)


class FlashSharedObject:
    """
    This class represents a Flash Remote Shared Object. Its data are located
    inside the self.data dictionary.
    """

    def __init__(self, name):
        """
        Initialize a new Flash Remote SO with a given name and empty data.
        """
        self.name = name
        self.data = {}
        self.use_success = False

    def use(self, reader, writer):
        """
        Initialize usage of the SO by contacting the Flash Media Server. Any
        remote changes to the SO should be now propagated to the client.
        """
        self.use_success = False

        msg = {
            'msg': DataTypes.SHARED_OBJECT,
            'curr_version': 0,
            'flags': '\x00\x00\x00\x00\x00\x00\x00\x00',
            'events': [
                {
                    'data': '',
                    'type': SOEventTypes.USE
                }
            ],
            'obj_name': self.name
        }
        writer.write(msg)
        writer.flush()

    def handle_message(self, message):
        """
        Handle an incoming RTMP message. Check if it is of any relevance for the
        specific SO and process it, otherwise ignore it.
        """
        if message['msg'] == DataTypes.SHARED_OBJECT and \
            message['obj_name'] == self.name:
            events = message['events']

            if not self.use_success:
                assert events[0]['type'] == SOEventTypes.USE_SUCCESS, events[0]
                assert events[1]['type'] == SOEventTypes.CLEAR, events[1]
                events = events[2:]
                self.use_success = True

            self.handle_events(events)
            return True
        else:
            return False

    def handle_events(self, events):
        """ Handle SO events that target the specific SO. """
        for event in events:
            event_type = event['type']
            if event_type == SOEventTypes.CHANGE:
                for key in event['data']:
                    self.data[key] = event['data'][key]
                    self.on_change(key)
            elif event_type == SOEventTypes.DELETE:
                key = event['data']
                assert key in self.data, (key,self.data.keys())
                del self.data[key]
                self.on_delete(key)
            elif event_type == SOEventTypes.MESSAGE:
                self.on_message(event['data'])
            else:
                assert False, event

    def on_change(self, key):
        pass

    def on_delete(self, key):
        pass

    def on_message(self, data):
        pass


class RtmpClient:
    """ Represents an RTMP client. """

    def __init__(self, ip, port, tc_url, page_url, swf_url, app):
        """ Initialize a new RTMP client. """
        self.ip = ip
        self.port = port
        self.tc_url = tc_url
        self.page_url = page_url
        self.swf_url = swf_url
        self.app = app
        self.shared_objects = []

        # superDebugNotice("rtmp client __init__")
        # superDebug("ip", self.ip)
        # superDebug("port", self.port)
        # superDebug("tc_url", self.tc_url)
        # superDebug("page_url", self.page_url)
        # superDebug("swf_url", self.swf_url)
        # superDebug("app", self.app)
        # superDebugFooter()

    def handshake(self):
        """ Perform the handshake sequence with the server. """

        # superDebugNotice("rtmp client handshake")

        self.stream.write_uchar(3)
        c1 = rtmp_protocol_base.Packet()
        c1.first = 0
        c1.second = 0
        c1.payload = 'x'*1528
        c1.encode(self.stream)
        self.stream.flush()

        # superDebug("c1 first", c1.first)
        # superDebug("c1 second", c1.second)
        # superDebug("c1 payload", c1.payload)

        self.stream.read_uchar()
        s1 = rtmp_protocol_base.Packet()
        s1.decode(self.stream)

        c2 = rtmp_protocol_base.Packet()
        c2.first = s1.first
        c2.second = s1.second
        c2.payload = s1.payload
        c2.encode(self.stream)
        self.stream.flush()

        # superDebug("c2 first", c2.first)
        # superDebug("c2 second", c2.second)
        # superDebug("c2 payload", c2.payload)

        s2 = rtmp_protocol_base.Packet()
        s2.decode(self.stream)

        # superDebugFooter()

    def connect_rtmp(self, connect_params):
        """ Initiate a NetConnection with a Flash Media Server. """
        msg = {
            'msg': DataTypes.COMMAND,
            'command':
            [
                u'connect',
                1,
                {
                    'videoCodecs': 252,
                    'audioCodecs': 3191,
                    'flashVer': u'WIN 10,1,85,3',
                    'app': self.app,
                    'tcUrl': self.tc_url,
                    'videoFunction': 1,
                    'capabilities': 239,
                    'pageUrl': self.page_url,
                    'fpad': False,
                    'swfUrl': self.swf_url,
                    'objectEncoding': 0
                }
            ]
        }

        # superDebugNotice("initiating rtmp connection")
        # superDebug("command", msg)
        # superDebug("connect_params", connect_params)

        msg['command'].extend(connect_params)
        self.writer.write(msg)
        self.writer.flush()

    def call(self, proc_name, parameters={}, trans_id=0):
        """ Runs remote procedure calls (RPC) at the receiving end. """
        msg = {
            'msg': DataTypes.COMMAND,
            'command':
            [
                proc_name,
                trans_id,
                parameters
            ]
        }

        # superDebug("calling RPC", msg)
        self.writer.write(msg)
        self.writer.flush()

    def handle_message_pre_connect(self, msg):
        """ Handle messages arriving before the connection is established. """
        if msg['msg'] == DataTypes.COMMAND:
            assert msg['command'][0] == '_result', msg
            assert msg['command'][1] == 1, msg
            assert msg['command'][3]['code'] == 'NetConnection.Connect.Success', msg
            return True

        elif msg['msg'] == DataTypes.WINDOW_ACK_SIZE:
            assert msg['window_ack_size'] == 2500000, msg
            return True

        elif msg['msg'] == DataTypes.SET_PEER_BANDWIDTH:
            assert msg['window_ack_size'] == 2500000, msg
            assert msg['limit_type'] == 2, msg
            return True

        elif msg['msg'] == DataTypes.USER_CONTROL:
            assert msg['event_type'] == UserControlTypes.STREAM_BEGIN, msg
            assert msg['event_data'] == '\x00\x00\x00\x00', msg
            return True

        elif msg['msg'] == DataTypes.SET_CHUNK_SIZE:
            assert 65536 >= msg['chunk_size'] > 0, msg
            self.reader.chunk_size = msg['chunk_size']
            self.writer.chunk_size = msg['chunk_size']
            return True
        else:
            assert False, msg

        return False

    def connect(self, connect_params):
        """ Connect to the server with the given connect parameters. """

        # superDebugNotice("rtmp client connect")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # superDebug("connecting with ip and port", (self.ip, self.port))
        self.socket.connect((self.ip, self.port))
        self.file = self.socket.makefile()
        self.stream = FileDataTypeMixIn(self.file)

        # superDebugNotice("performing handshake")
        self.handshake()

        # superDebugNotice("creating reader")
        self.reader = RtmpReader(self.stream)
        # superDebugNotice("creating writer")
        self.writer = RtmpWriter(self.stream)

        # superDebugNotice("performing rtmp connect")
        self.connect_rtmp(connect_params)

        # superDebugFooter()

    def shared_object_use(self, so):
        """ Use a shared object and add it to the managed list of SOs. """
        if so in self.shared_objects:
            return
        so.use(self.reader, self.writer)
        self.shared_objects.append(so)

    def handle_messages(self):
        """ Start the message handling loop. """
        while True:
            msg = self.reader.next()

            handled = self.handle_simple_message(msg)

            if handled:
                continue

            for so in self.shared_objects:
                if so.handle_message(msg):
                    handled = True
                    break
            if not handled:
                assert False, msg

    def handle_simple_message(self, msg):
        """ Handle simple messages, e.g. ping requests. """
        if msg['msg'] == DataTypes.USER_CONTROL and msg['event_type'] == \
                UserControlTypes.PING_REQUEST:
            resp = {
                'msg':DataTypes.USER_CONTROL,
                'event_type':UserControlTypes.PING_RESPONSE,
                'event_data':msg['event_data'],
            }
            self.writer.write(resp)
            self.writer.flush()
            return True

        return False
