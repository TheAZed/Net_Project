"""

    This is the format of packets in our network:
    


                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1
    
    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'
    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:
    
        Register:
            Request:
        
                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________|
                
                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:
        
                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________|
                
                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________|
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________|
                
                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.


            
        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|
                
                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:
        
                                    ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.
            
    
"""
from struct import *

import struct

from src.tools.Node import Node


class Packet:

    def __init__(self, buf=None, version=None, type=None, length=None, source_server_ip=None, source_server_port=None,
                 body=None):
        """
        The decoded buffer should convert to a new packet.

        :param buf: Input buffer was just decoded.
        :type buf: bytes
        """
        if buf is not None:
            self.buf = buf
            data = struct.unpack('!hhl4hl', bytes(buf[:20]))
            self.version = data[0]
            self.type = data[1]
            self.length = data[2]
            ip_str_list = [chr(i) for i in data[3:7]]
            ip_str = ip_str_list[0] + '.' + ip_str_list[1] + '.' + ip_str_list[2] + '.' + ip_str_list[3]
            self.source_server_ip = Node.parse_ip(ip_str)
            self.source_server_port = Node.parse_port(str(data[7]))
            rest = struct.unpack('%dB' % len(buf[20:]), buf[20:])
            self.body = ''.join(chr(i) for i in rest)
        else:
            self.version = version
            self.type = type
            self.length = length
            self.source_server_ip = source_server_ip
            self.source_server_port = source_server_port
            self.body = body
            ip_int_list = list(map(int, self.source_server_ip.split('.')))
            self.buf = struct.pack('!hhl4hl%dB' % len(body), version, type, length, *ip_int_list,
                                   int(source_server_port), *bytes(body, 'utf-8'))
        pass

    def get_header(self):
        """

        :return: Packet header
        :rtype: str
        """
        # FIXME What should we return here?
        pass

    def get_version(self):
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version
        pass

    def get_type(self):
        """

        :return: Packet type
        :rtype: int
        """
        return self.type
        pass

    def get_length(self):
        """

        :return: Packet length
        :rtype: int
        """
        return self.length
        pass

    def get_body(self):
        """

        :return: Packet body
        :rtype: str
        """
        return self.body
        pass

    def get_buf(self):
        """
        In this function, we will make our final buffer that represents the Packet with the Struct class methods.

        :return The parsed packet to the network format.
        :rtype: bytearray
        """
        return self.buf
        pass

    def get_source_server_ip(self):
        """

        :return: Server IP address for the sender of the packet.
        :rtype: str
        """
        return self.source_server_ip
        pass

    def get_source_server_port(self):
        """

        :return: Server Port address for the sender of the packet.
        :rtype: str
        """
        return self.source_server_port
        pass

    def get_source_server_address(self):
        """

        :return: Server address; The format is like ('192.168.001.001', '05335').
        :rtype: tuple
        """
        return self.source_server_ip, self.source_server_port
        pass


class PacketFactory:
    """
    This class is only for making Packet objects.
    """

    @staticmethod
    def parse_buffer(buffer):
        """
        In this function we will make a new Packet from input buffer with struct class methods.

        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype Packet

        """
        return Packet(buf=buffer)
        pass

    @staticmethod
    def new_reunion_packet(type, source_address, nodes_array):
        """
        :param type: Reunion Hello (REQ) or Reunion Hello Back (RES)
        :param source_address: IP/Port address of the packet sender.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :type type: str
        :type source_address: tuple
        :type nodes_array: list

        :return New reunion packet.
        :rtype Packet
        """
        packet_body = ''
        packet_body += type
        packet_body += str(len(nodes_array)).zfill(width=2)
        for address in nodes_array:
            packet_body += Node.parse_ip(address[0])
            packet_body += Node.parse_port(address[1])
        packet = None
        if type == 'REQ' or type == 'RES':
            packet = Packet(None, 1, 5, 5 + 20 * len(nodes_array), source_address[0], source_address[1], packet_body)
        else:
            print("Invalid Reunion Packet Type!")
        return packet
        pass

    @staticmethod
    def new_advertise_packet(type, source_server_address, neighbour=None):
        """
        :param type: Type of Advertise packet - Either 'REQ' or 'RES'
        :param source_server_address: Server address of the packet sender.
        :param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type neighbour: tuple

        :return New advertise packet.
        :rtype Packet

        """

        packet_body = type

        #packet_body=type+packet_body
        packet = None

        if type == 'REQ':
            packet = Packet(None, 1, 2, 3, source_server_address[0], source_server_address[1], packet_body)
        elif type == 'RES':
            packet_body += neighbour[0] + neighbour[1]
            packet = Packet(None, 1, 2, 23, source_server_address[0], source_server_address[1], packet_body)
        else:
            print("Invalid Advertise Packet Type!")
        return packet
        pass

    @staticmethod
    def new_join_packet(source_server_address):
        """
        :param source_server_address: Server address of the packet sender.

        :type source_server_address: tuple

        :return New join packet.
        :rtype Packet

        """
        packet = Packet(None, 1, 3, 4, source_server_address[0], source_server_address[1], 'JOIN')
        return packet
        pass

    @staticmethod
    def new_register_packet(type, source_server_address, address=(None, None)):
        """
        :param type: Type of Register packet - Either 'REQ' or 'RES'
        :param source_server_address: Server address of the packet sender.
        :param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type address: tuple

        :return New Register packet.
        :rtype Packet

        """
        packet_body = ''
        packet_body += type
        packet = None
        if type == 'REQ':
            packet_body = packet_body + source_server_address[0] + source_server_address[1]
            packet = Packet(None, 1, 1, 23, source_server_address[0], source_server_address[1], packet_body)
        elif type == 'RES':
            packet_body += 'ACK'
            packet = Packet(None, 1, 1, 6, source_server_address[0], source_server_address[1], packet_body)
        else:
            print("Invalid Register Packet Type!")
        return packet
        pass

    @staticmethod
    def new_message_packet(message, source_server_address):
        """
        Packet for sending a broadcast message to the whole network.

        :param message: Our message
        :param source_server_address: Server address of the packet sender.

        :type message: str
        :type source_server_address: tuple

        :return New Message packet.
        :rtype Packet
        """
        packet = Packet(None, 1, 4, len(message), source_server_address[0], source_server_address[1], message)
        return packet
        pass
