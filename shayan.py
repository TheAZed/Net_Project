from src.Packet import *

packet = PacketFactory.new_advertise_packet("RES",("127.000.000.001", "05356"), ("127.000.000.001", "31315"))
print(packet.get_buf())
