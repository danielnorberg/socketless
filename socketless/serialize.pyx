# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

import struct

from cpython.list cimport *
from cpython.ref cimport *

cdef object int32_unpack = struct.Struct('!L').unpack
cdef object int64_unpack = struct.Struct('!Q').unpack

cpdef str_info(s):
    return 0xFFFFFFFF if s is None else len(s)

cpdef pack_str(s):
    return '' if s is None else s

cdef class MessageReader:
    """docstring for MessageReader"""
    def __init__(self, message):
        self.message = message
        self.i = 0

    cdef inline object _read(self, unsigned long length):
        # assert self.message
        # assert self.i + length <= len(self.message)
        if length > 1024:
            data = buffer(self.message, self.i, length)
        else:
            data = self.message[self.i:self.i+length]
        self.i += length
        return data

    cdef inline object _read_string(self):
        return self._read(self.read_int32())

    cdef inline unsigned long read_int(self):
        return self.read_int32()

    cdef inline unsigned long read_int32(self):
        return int32_unpack(self._read(4))[0]

    cdef inline unsigned long long read_int64(self):
        return int64_unpack(self._read(8))[0]

    cpdef inline object read(self, unsigned long length=0):
        if length == 0:
            length = len(self.message) - self.i
        return self._read(length)

    cpdef inline object read_string(self):
        cdef unsigned int string_length = self.read_int32()
        if string_length == 0xFFFFFFFF:
            return None
        else:
            return self._read(string_length)



cdef class MarshallerGenerator(object):
    """docstring for Marshaller"""
    def __init__(self):
        super(MarshallerGenerator, self).__init__()

    cpdef tuple compile(self, format):
        if not len(format):
            return (eval('lambda *args:""', {}), eval('lambda *args:None', {}))

        parameter_names = [name for name, typ in format]
        marshalling_segments = self.marshalling_segments(format)
        unmarshalling_segments = self.unmarshalling_segments(format)

        segment_unpackers = dict(('unpack_%s' % name, s.unpack) for name, exprs, s in unmarshalling_segments if s != str)
        segment_packers = dict(('pack_%s' % name, s.pack) for name, exprs, s in marshalling_segments if s != str)
        marshal_operations = ['pack_%s(%s)' % (name, ','.join(exprs)) if s != str else ','.join(['pack_str(%s)' % expr for expr in exprs]) for name, exprs, s in marshalling_segments]
        unmarshal_operations = ['unpack_%s(reader.read(%d))' % (name, s.size) if s != str else 'reader.read_string()' for name, exprs, s in unmarshalling_segments]

        marshal_env = segment_packers
        unmarshal_env = segment_unpackers

        marshal_env['str_info'] = str_info
        marshal_env['pack_str'] = pack_str

        marshal_template = "def %s(%s): \n"\
                           "    return %s\n"


        unmarshal_template = "def %s(reader):\n"\
                             "    %s = %s\n"\
                             "    return %s\n"

        marshal_name = 'marshal_%s' % '_'.join(parameter_names)
        unmarshal_name = 'unmarshal_%s' % '_'.join(parameter_names)
        parameter_list = ','.join(parameter_names)
        marshal_code = marshal_template % (marshal_name, parameter_list, ', '.join(marshal_operations))
        unmarshal_code = unmarshal_template % (unmarshal_name, parameter_list, ', '.join(unmarshal_operations), parameter_list)

        # print marshal_code
        # print unmarshal_code

        marshal_code_compiled = compile(marshal_code, 'serialize.MarshallerGenerator.compile.marshal', 'exec')
        unmarshal_code_compiled = compile(unmarshal_code, 'serialize.MarshallerGenerator.compile.unmarshal', 'exec')

        exec marshal_code_compiled in marshal_env
        exec unmarshal_code_compiled in unmarshal_env

        marshal_function = marshal_env[marshal_name]
        unmarshal_function = unmarshal_env[unmarshal_name]

        return (marshal_function, unmarshal_function)

    cdef compile_segment(self, segment):
        segment_name = '_'.join([name for name, expr, typ in segment])
        expressions = [expr for name, expr, typ in segment]
        types = [typ for name, expr, typ in segment]
        s = struct.Struct('!' + ''.join(types)) if types[0] != str else str
        return (segment_name, expressions, s)

    cdef unmarshalling_segments(self, format):
        segment = []
        segments = []
        for name, typ in format:
            if typ is str:
                if segment:
                    segments.append(self.compile_segment(segment))
                    segment = []
                segments.append(self.compile_segment([(name, name, str)]))
            elif typ is int:
                segment.append((name, name, 'L'))
            elif typ is long:
                segment.append((name, name, 'Q'))
            else:
                raise Exception("Cannot handle parameter '%s' of type '%s'", name, typ)
        if segment:
            segments.append(self.compile_segment(segment))
        return segments

    cdef marshalling_segments(self, format):
        segment = []
        segments = []
        for name, typ in format:
            if typ is str:
                segment.append(('len_%s' % name, 'str_info(%s)' % name, 'L'))
                segments.append(self.compile_segment(segment))
                segments.append(self.compile_segment([(name, name, str)]))
                segment = []
            elif typ is int:
                segment.append((name, name, 'L'))
            elif typ is long:
                segment.append((name, name, 'Q'))
            else:
                raise Exception("Cannot handle parameter '%s' of type '%s'", name, typ)
        if segment:
            segments.append(self.compile_segment(segment))
        return segments
