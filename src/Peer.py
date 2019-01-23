from src.Stream import Stream
from src.Packet import Packet, PacketFactory
from src.UserInterface import UserInterface
from src.tools.Node import Node
from src.tools.NetworkGraph import NetworkGraph, GraphNode
import time
import copy

"""
    Peer is our main object in this project.
    In this network Peers will connect together to make a tree graph.
    This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.
    
"""


class Peer:
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):

        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.@@@@@@@
            4. Initialise a Thread for handling reunion daemon.@@@@@@@@

        Warnings:
            1. For root Peer, we need a NetworkGraph object.@@@@@@@@@@@
            2. In root Peer, start reunion daemon as soon as possible.@@@@@@@@@@@
            3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
               as a register_connection.


        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: tuple
        """
        self.time_out = 40
        self.user_interface = UserInterface()
        self.server_ip = Node.parse_ip(server_ip)
        self.server_port = Node.parse_port(str(server_port))
        self.is_root = is_root

        self.stream = Stream(ip=server_ip, port=server_port)
        self.user_interface = UserInterface()
        self.registered = False
        self.state = 'newborn'

        self.life = False  # while self.life : run
        self.counter = 0  # when to send in run
        self.parent_address = None
        self.left_child = None
        self.right_child = None
        self.reunion_on_fly = False
        self.connection_timer = None
        self.start_user_interface()
        if self.is_root:
            self.life = True
            self.registered_addresses = []
            self.graph_node = GraphNode(address=(self.server_ip, self.server_port))
            self.network_graph = NetworkGraph(root=self.graph_node)
            self.root_ip = self.server_ip
            self.root_port = self.server_port
            self.state = 'joined'

        else:
            self.root_ip = Node.parse_ip(root_address[0])
            self.root_port = Node.parse_port(str(root_address[1]))
            self.client_start()
        self.run()
        pass

    def start_user_interface(self):
        self.user_interface.start()

        """
        For starting UserInterface thread.

        :return:
        """
        pass

    def handle_user_interface_buffer(self):
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network

        Warnings:
            1. Ignore irregular commands from the user.
            2. Don't forget to clear our UserInterface buffer.
        :return:
        """
        for message in self.user_interface.buffer:
            if message.startswith('Register'):
                #
                # splited_message=message.split()
                # if len(splited_message)==3:
                #     self.root_ip=splited_message[1]
                #     self.root_ip=splited_message[2]
                if self.state == 'newborn':
                    out_packet = PacketFactory.new_register_packet(type='REQ',
                                                                   source_server_address=self.get_server_address(),
                                                                   address=self.get_root_address())
                    self.stream.add_node(server_address=self.get_root_address(), set_register_connection=True)
                    self.stream.add_message_to_out_buff(address=self.get_root_address(), message=out_packet.get_buf())
                else:
                    print("You are already registered!")

            if message.startswith('Advertise'):
                if self.state == 'registered':
                    out_packet = PacketFactory.new_advertise_packet(type='REQ',
                                                                    source_server_address=self.get_server_address())
                    self.stream.add_message_to_out_buff(address=self.get_root_address(), message=out_packet.get_buf())
                else:
                    print("Either you are already advertised or you are not registered yet!")

            if message.startswith('SendMessage'):
                if self.state == 'joined':
                    out_packet = PacketFactory.new_message_packet(message=message[11:],
                                                                  source_server_address=self.get_server_address())
                    self.send_broadcast_packet(broadcast_packet=out_packet)
                else:
                    print("You need to be joined with the network to send broadcasts!")

            if message.startswith('disconnect'):
                pass
        self.user_interface.buffer.clear()

    def client_start(self):

        self.life = True

    def run(self):
        """
        The main loop of the program.

        Code design suggestions:
            1. Parse server in_buf of the stream.
            2. Handle all packets were received from our Stream server.
            3. Parse user_interface_buffer to make message packets.
            4. Send packets stored in nodes buffer of our Stream object.
            5. ** sleep the current thread for 2 seconds **

        Warnings:
            1. At first check reunion daemon condition; Maybe we have a problem in this time
               and so we should hold any actions until Reunion acceptance.
            2. In every situation checkout Advertise Response packets; even is Reunion in failure mode or not

        :return:
        """

        while self.life:
            # print("@@@ Time %4 =  " + str(self.counter) +
            #       "  /  State = " + self.state +
            #       "  /  connection_timer = " + str(self.connection_timer) +
            #       "  /  you_root = " + str(self.is_root) +
            #       "  /  your_address = " + str(self.get_server_address()) +
            #       "  /  your_parent = " + str(self.parent_address) +
            #       "  /  your_left_child = " + str(self.left_child) +
            #       "  /  your_address = " + str(self.right_child))
            if self.is_root:
                addresses = self.network_graph.nodes.keys()
                entries_to_remove = []
                for key in addresses:
                    if self.network_graph.nodes.keys().__contains__(key) \
                            and self.network_graph.nodes[key].reunion_timer > self.time_out:
                        # self.(node_address=self.network_graph.nodes[key].address)
                        if key != self.get_server_address():
                            entries_to_remove.append(key)
                        # TODO belakhare nafahmidam khaje ro
                for entry in entries_to_remove:
                    self.network_graph.remove_node(entry)

            if not self.is_root and self.connection_timer is not None and self.connection_timer > self.time_out:
                self.deep_disconnect()
                print("Timeout Detected. Sending new Advertise Request!")
                out_packet = PacketFactory.new_advertise_packet(type='REQ', source_server_address=(
                    self.server_ip, self.server_port))
                self.stream.add_message_to_out_buff(address=self.get_root_address(), message=out_packet.get_buf())

            if self.counter == 2 or self.counter == 0:
                self.handle_user_interface_buffer()
                buffs = self.stream.read_in_buf()
                packs = []

                for i in range(len(buffs)):
                    packs.append(PacketFactory.parse_buffer(buffs[i]))

                for i in range(len(buffs)):
                    self.handle_packet(packs[i])

                if not self.is_root and self.state == 'joined' and self.connection_timer >= 0 and not self.reunion_on_fly:
                    self.send_reunion_client()
                    # print(" New reunion_packet sent")

                self.stream.clear_in_buff()
                problematic_nodes = self.stream.send_out_buf_messages()
                for node in problematic_nodes:
                    if not node.is_root and node.get_server_address() != self.get_root_address():
                        print("Removing problematic node: " + str(node.get_server_address()))
                        if self.is_root:
                            self.network_graph.remove_node(node.get_server_address())
                        self.stream.remove_node(node)
                        if self.left_child == node.get_server_address():
                            self.left_child = None
                        elif self.right_child == node.get_server_address():
                            self.right_child = None
                        elif self.parent_address == node.get_server_address():
                            self.deep_disconnect()
                            print("Disconnection Detected. Sending new Advertise Request!")
                            out_packet = PacketFactory.new_advertise_packet(type='REQ', source_server_address=(
                                self.server_ip, self.server_port))
                            self.stream.add_message_to_out_buff(self.get_root_address(), out_packet.get_buf())

                    else:
                        print("Sir we're facing a dire situation. it seems the HQ is taken down and we've lost the war")
                        exit(0)

            self.counter += 1
            if self.counter == 4:
                self.counter = 0

            if self.connection_timer is not None:
                self.connection_timer += 1

            if self.is_root:
                for kk in self.network_graph.nodes.keys():
                    self.network_graph.nodes[kk].reunion_timer += 1

            time.sleep(1)

        pass

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            1. Check if we are the network root or not; The actions are identical.
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """
        pass

    def send_reunion_client(self):

        self.connection_timer = 0
        self.reunion_on_fly = True
        ms = PacketFactory.new_reunion_packet(type='REQ', source_address=(self.server_ip, self.server_port),
                                              nodes_array=[(self.server_ip, self.server_port)])
        self.stream.add_message_to_out_buff(address=self.parent_address, message=ms.get_buf())
        print("Sent Reunion Packet to Parent: " + str(self.parent_address))

    def send_broadcast_packet(self, broadcast_packet, except_address=None):

        """

        For setting broadcast packets buffer into Nodes out_buff.

        Warnings:
            1. Don't send Message packets through register_connections.

        :param broadcast_packet: The packet that should be broadcast through the network.
        :type broadcast_packet: Packet
        :param except_address: The address from which this message has come
        :type except_address: tuple

        :return:
        """
        print("Sending Broadcast Message: " + broadcast_packet.get_body())
        if self.parent_address is not None and self.parent_address != except_address:
            self.stream.add_message_to_out_buff(address=self.parent_address, message=broadcast_packet.get_buf())
            # print("Message packet recieved from "+broadcast_source+"  .  Broadcasted to parent : "+self.parent_address)

        if self.left_child is not None and self.left_child != except_address:
            self.stream.add_message_to_out_buff(address=self.left_child, message=broadcast_packet.get_buf())
            # print("Message packet recieved from "+broadcast_source+"  .  Broadcasted to left child : "+self.left_child)

        if self.right_child is not None and self.right_child != except_address:
            self.stream.add_message_to_out_buff(address=self.right_child, message=broadcast_packet.get_buf())
            # print("Message packet recieved from "+broadcast_source+"  .  Broadcasted to right child : "+self.right_child)

        pass

    def __check_registered(self, source_address):
        """
        If the Peer is the root of the network we need to find that if a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: tuple

        :return:
        """

        # FIXME in tabe daghighan chie
        if source_address not in self.registered_addresses:
            print("Unregistered message received from: " + str(source_address))
            return False
        return True
        pass

    def handle_packet(self, packet):
        """

        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """

        ########packet validation :

        if packet.type == 1:
            self.__handle_register_packet(packet)

        if packet.type == 2:
            self.__handle_advertise_packet(packet)

        if packet.type == 3:
            self.__handle_join_packet(packet)

        if packet.type == 4:
            self.__handle_message_packet(packet)

        if packet.type == 5:
            self.__handle_reunion_packet(packet)

        pass

    def __handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

        Warnings:
            1. Don't forget to ignore Register Request packets when you are a non-root peer.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """

        if self.is_root and packet.get_body()[0:3] == 'REQ':

            ack = self.__check_registered(packet.get_source_server_address())
            if not ack:
                self.stream.add_node(server_address=packet.get_source_server_address(), set_register_connection=True)
                out_packet = PacketFactory.new_register_packet(type='RES',
                                                               source_server_address=(self.server_ip, self.server_port))
                self.stream.add_message_to_out_buff(address=packet.get_source_server_address(),
                                                    message=out_packet.get_buf())
                self.registered_addresses.append(packet.get_source_server_address())

                print("register,REQ  packet from client : " + str(packet.get_source_server_address()) + "  ACK: " +
                      str(ack) + "  RESPONDED succesfully")
            else:
                print("Duplicate register packet received from: " + str(packet.get_source_server_address()))

        elif not self.is_root and self.state == 'newborn' and packet.get_body()[0:3] == 'RES':
            self.state = 'registered'
            # out_packet = PacketFactory.new_advertise_packet(type='REQ',
            #                                                 source_server_address=(self.server_ip, self.server_port))
            # self.stream.add_message_to_out_buff(address=self.get_root_address(), message=out_packet.get_buf())
            print(" register,RES packet  from root . ACK = " + packet.get_body()[3:6] + " received.")
        else:
            print("Invalid register packer received!")

    def __handle_advertise_packet(self, packet):
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        Code design suggestion:
            1. Start the Reunion daemon thread when the first Advertise Response packet received.
            2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

        Warnings:
            1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.
            4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """

        if self.is_root and packet.get_body()[0:3] == 'REQ':

            if not self.__check_registered(packet.get_source_server_address()):
                print("Unregistered Advertise Packet Received!")
                return

            # IT SEEMS WE HAVE TO RESET THE NODE EVERY TIME A DUPLICATE ADVERTISE IS RECEIVED

            # if self.network_graph.nodes.keys().__contains__(packet.get_source_server_address()) and \
            #         self.network_graph.nodes[packet.get_source_server_address()].alive:
            #     print(" REQ Advertised packet recieved . dropped because it's already in graph node and turned on")
            #     return

            if packet.get_source_server_address() in self.network_graph.nodes.keys():
                print("Received Dup Advertise. Resetting Client: " + str(packet.get_source_server_address()))
                father = self.network_graph.restart_node(packet.get_source_server_address())
            else:
                father = self.network_graph.find_live_node()
                self.network_graph.add_node(ip=packet.get_source_server_address()[0],
                                            port=packet.get_source_server_address()[1], father_address=father.address)
                self.network_graph.turn_on_node(packet.get_source_server_address())

            out_packet = PacketFactory.new_advertise_packet(type='RES', source_server_address=self.get_server_address(),
                                                            neighbour=father.address)
            self.stream.add_message_to_out_buff(address=packet.get_source_server_address(),
                                                message=out_packet.get_buf())

            # self.stream.remove_node(node=self.stream.get_node_by_server(ip=packet.get_source_server_ip(),port=packet.get_source_server_port()))
            # TODO khaje goft server she root !!!!
            print("advertise packet REQ , recieved from  client :  " + str(packet.get_source_server_address()) +
                  ". Client " + str(father.address) + " is chosen as its father.")

        elif not self.is_root and self.state == 'registered' and packet.get_body()[0:3] == 'RES':
            self.state = 'advertised'
            self.stream.add_node(server_address=(packet.get_body()[3:18], packet.get_body()[18:23]),
                                 set_register_connection=False)
            out_packet = PacketFactory.new_join_packet(source_server_address=(self.server_ip, self.server_port))
            self.stream.add_message_to_out_buff(address=(packet.get_body()[3:18], packet.get_body()[18:23]),
                                                message=out_packet.get_buf())
            self.parent_address = (packet.get_body()[3:18], packet.get_body()[18:23])
            self.state = 'joined'
            self.connection_timer = -4
            print("Advertise packet RES from root , recieved . Client " + str(self.parent_address) +
                  " is chosen as your parent. state changed to joined and Join packet sent to parent.")

    def __handle_join_packet(self, packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network.

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """

        if self.left_child is None:
            self.stream.add_node(server_address=packet.get_source_server_address(), set_register_connection=False)
            self.left_child = packet.get_source_server_address()
            print("Client  " + str(packet.get_source_server_address()) + "  is joined as your left child .")
        elif self.right_child is None:
            self.stream.add_node(server_address=packet.get_source_server_address(), set_register_connection=False)
            self.right_child = packet.get_source_server_address()
            print("Client  " + str(packet.get_source_server_address()) + "  is joined as your right child .")
        else:
            print("You have 2 joined children but client " + str(packet.get_source_server_address()) +
                  "  wants to join you!!!.")

    def __handle_reunion_packet(self, packet):
        """
        In this function we should handle Reunion packet was just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
            If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

        Reunion Hello Back:
            Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
            address, otherwise you received your response from the root and everything is fine.

        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
            3. If you are the end node, update your Reunion mode from pending to acceptance.


        :param packet: Arrived reunion packet
        :return:
        """

        body = packet.get_body()

        if not self.__check_neighbour(address=packet.get_source_server_address()):
            print("Reunion packet from stranger . dropped !!!")
            return

        if self.is_root and body[0:3] == 'REQ':

            if not self.network_graph.nodes.keys().__contains__(packet.get_source_server_address()):
                print("Reunion,REQ packet from client : " + str(packet.get_source_server_address()) +
                      "  .   Source_address doesn't exist in network_graph.")
                return

            if not self.network_graph.nodes[packet.get_source_server_address()].alive:
                print("Reunion,REQ packet from client : " + str(packet.get_source_server_address()) +
                      "  .   Source_address node in network_graph is turned_off.")
                return

            node_list = []
            for i in range(int(body[3:5])):
                node_list.append((body[5 + 20 * i:20 + 20 * i], body[20 + 20 * i:25 + 20 * i]))
            node_list.reverse()
            self.network_graph.nodes[node_list[len(node_list) - 1]].reunion_timer = 0
            ms = PacketFactory.new_reunion_packet(source_address=self.get_root_address(), type='RES',
                                                  nodes_array=node_list).get_buf()
            self.stream.add_message_to_out_buff(address=packet.get_source_server_address(), message=ms)
            print("Reunion,REQ packet from client : " + str(node_list[len(node_list) - 1]) +
                  "  .  Node.reunion_timer in network_graph reseted to 0 successfully and RES reunion sent to client.")

        if not self.is_root and body[0:3] == 'REQ':

            if not self.state == 'joined':
                print("Reunion,REQ packet received from client : " + str(packet.get_source_server_address()) +
                      " .  But you are not joined thus reunion packet is dropped.")
                return

            node_list = []
            for i in range(int(body[3:5])):
                node_list.append((body[5 + 20 * i:20 + 20 * i], body[20 + 20 * i:25 + 20 * i]))

            node_list.append((self.server_ip, self.server_port))

            ms = PacketFactory.new_reunion_packet(source_address=self.get_server_address(), type='REQ',
                                                  nodes_array=node_list).get_buf()
            self.stream.add_message_to_out_buff(address=self.parent_address, message=ms)
            print("Reunion REQ packet received from client : " + str(packet.get_source_server_address()) +
                  "  and successfully directed to parent :  " + str(self.parent_address))

        if not self.is_root and body[0:3] == 'RES':
            if not self.state == 'joined':
                print("Reunion RES packet recieved from client : " + str(packet.get_source_server_address()) +
                      " .  But you are not joined thus reunion packet is dropped .")
                return

            if int(body[3:5]) == 1:
                if body[5:20] == self.server_ip and body[20:25] == self.server_port:
                    self.connection_timer = -4
                    self.reunion_on_fly = False
                    print("Reunion RES packet recieved from yourself recieved to yourself and connection_timer reset" +
                          " to -4 . ")
                else:
                    print("Invalid Reunion Hello packet received. there must be a problem in packet forwarding.")

            else:
                node_list = []
                for i in range(1, int(body[3:5])):
                    node_list.append((body[5 + 20 * i:20 + 20 * i], body[20 + 20 * i:25 + 20 * i]))

                ms = PacketFactory.new_reunion_packet(source_address=self.get_server_address(),
                                                      type='RES', nodes_array=node_list).get_buf()

                if self.left_child is not None and body[25:40] == self.left_child[0] and body[40:45] == \
                        self.left_child[1]:
                    self.stream.add_message_to_out_buff(address=self.left_child, message=ms)
                    print("Reunion RES packet received from client : " + str(packet.get_source_server_address()) +
                          "  . mirrored to left child successfully.")

                elif self.right_child is not None and body[25:40] == self.right_child[0] and body[40:45] == \
                        self.right_child[1]:
                    self.stream.add_message_to_out_buff(address=self.right_child, message=ms)
                    print("Reunion RES packet received from client : " + str(packet.get_source_server_address()) +
                          "  . mirrored to right child successfully.")

                else:
                    print("Reunion RES packet recieved from client : " + str(packet.get_source_server_address()) +
                          " . But it should not be mirrored to neither of your children!!!!!")

        pass

    def __handle_message_packet(self, packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet: Packet

        :return:
        """

        if not self.__check_neighbour(address=packet.get_source_server_address()):
            print("Message packet from stranger . dropped !!!")
            return

        out_packet = PacketFactory.new_message_packet(message=packet.get_body(),
                                                      source_server_address=self.get_server_address())
        self.send_broadcast_packet(out_packet, packet.get_source_server_address())
        # broadcast_source = "@@@"
        # if packet.get_source_server_address() == self.parent_address:
        #     broadcast_source = "parent"
        # if packet.get_source_server_address() == self.left_child:
        #     broadcast_source = "left child"
        # if packet.get_source_server_address() == self.right_child:
        #     broadcast_source = "right child"
        #
        # if self.parent_address is not None and not (
        #                 self.parent_address[0] == packet.get_source_server_address()[0] and self.parent_address[1] ==
        #             packet.get_source_server_address()[1]):
        #     self.stream.add_message_to_out_buff(address=self.parent_address, message=out_packet.get_buf())
        #     print(
        #             "Message packet recieved from " + broadcast_source + "  .  Broadcasted to parent : " + self.parent_address)
        # if self.left_child is not None and not (
        #                 self.left_child[0] == packet.get_source_server_address()[0] and self.left_child[1] ==
        #             packet.get_source_server_address()[1]):
        #     self.stream.add_message_to_out_buff(address=self.left_child, message=out_packet.get_buf())
        #     print(
        #             "Message packet recieved from " + broadcast_source + "  .  Broadcasted to left child : " + self.left_child)
        #
        # if self.right_child is not None and not (
        #                 self.right_child[0] == packet.get_source_server_address()[0] and self.right_child[1] ==
        #             packet.get_source_server_address()[1]):
        #     self.stream.add_message_to_out_buff(address=self.right_child, message=out_packet.get_buf())
        #     print(
        #             "Message packet recieved from " + broadcast_source + "  .  Broadcasted to right child : " + self.right_child)

        print("Message body  :  " + packet.get_body())

    def __check_neighbour(self, address):
        """
        It checks is the address in our neighbours array or not.

        :param address: Unknown address

        :type address: tuple

        :return: Whether is address in our neighbours or not.
        :rtype: bool
        """

        return self.parent_address == address or self.left_child == address or self.right_child == address
        pass

    def __get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
        """

        return self.network_graph.find_live_node().address

        pass

    def get_root_address(self):
        return self.root_ip, self.root_port

    def get_root_ip(self):
        return self.root_ip

    def get_root_port(self):
        return self.root_port

    def get_server_address(self):
        return self.server_ip, self.server_port

    def deep_disconnect(self):
        self.reunion_on_fly = False
        if self.parent_address is not None:
            node = self.stream.get_node_by_server(self.parent_address[0], self.parent_address[1])
            if node is not None:
                self.stream.remove_node(node)
            self.parent_address = None
        if self.left_child is not None:
            node = self.stream.get_node_by_server(self.left_child[0], self.left_child[1])
            if node is not None:
                self.stream.remove_node(node)
            self.left_child = None
        if self.right_child is not None:
            node = self.stream.get_node_by_server(self.right_child[0], self.right_child[1])
            if node is not None:
                self.stream.remove_node(node)
            self.right_child = None
        self.connection_timer = None
        self.state = 'registered'

