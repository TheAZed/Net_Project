from src.tools.simpletcp.tcpserver import TCPServer

from src.tools.Node import Node
import threading


class Stream:
    def __init__(self, ip, port):
        """
        The Stream object constructor.

        Code design suggestion:
            1. Make a separate Thread for your TCPServer and start immediately.


        :param ip: 15 characters
        :param port: 5 characters
        """

        self.ip = Node.parse_ip(ip)
        self.port = Node.parse_port(port)

        self._server_in_buf = []

        def callback(address, queue, data):
            """
            The callback function will run when a new data received from server_buffer.

            :param address: Source address.
            :param queue: Response queue.
            :param data: The data received from the socket.
            :return:
            """
            queue.put(bytes('ACK', 'utf8'))
            self._server_in_buf.append(data)

        self.tcp_server = TCPServer(self.ip, int(self.port), callback)
        self.server_thread = threading.Thread(target=self.tcp_server.run)
        self.server_thread.start()

        self.nodes = []
        pass

    def get_server_address(self):
        """

        :return: Our TCPServer address
        :rtype: tuple
        """
        return self.ip, self.port

    def clear_in_buff(self):
        """
        Discard any data in TCPServer input buffer.

        :return:
        """
        self._server_in_buf.clear()

    def add_node(self, server_address: object, set_register_connection: object = False) -> object:
        # FIXME check kon age ba in adress node dashtim moshkel pish naiad o node dobare alaki nasaze
        """
        Will add new a node to our Stream.

        :param server_address: New node TCPServer address.
        :param set_register_connection: Shows that is this connection a register_connection or not.

        :type server_address: tuple
        :type set_register_connection: bool

        :return:
        """
        # FIXME when should a node be marked as root?
        if self.get_node_by_server(server_address[0], server_address[1]) is not None:
            print("A Node with ip: " + server_address[0] + " and port: " + server_address[1] + " already exists!")
            return
        try:
            new_node = Node(server_address, set_register=set_register_connection)
        except ConnectionRefusedError:
            print("This address does not exist in network! " + str(server_address))
            return
        self.nodes.append(new_node)
        pass

    def remove_node(self, node):
        """
        Remove the node from our Stream.

        Warnings:
            1. Close the node after deletion.

        :param node: The node we want to remove.
        :type node: Node

        :return:
        """
        self.nodes.remove(node)
        node.close()
        pass

    def get_node_by_server(self, ip, port):
        """

        Will find the node that has IP/Port address of input.

        Warnings:
            1. Before comparing the address parse it to a standard format with Node.parse_### functions.

        :param ip: input address IP
        :param port: input address Port

        :return: The node that input address.
        :rtype: Node
        """
        p_ip = Node.parse_ip(ip)
        p_port = Node.parse_port(port)
        the_node = None
        for node in self.nodes:
            if node.server_ip == p_ip and node.server_port == p_port:
                the_node = node
                break
        return the_node
        pass

    def add_message_to_out_buff(self, address, message):
        """
        In this function, we will add the message to the output buffer of the node that has the input address.
        Later we should use send_out_buf_messages to send these buffers into their sockets.

        :param address: Node address that we want to send the message
        :param message: Message we want to send

        Warnings:
            1. Check whether the node address is in our nodes or not.

        :return:
        """
        node = self.get_node_by_server(address[0], address[1])
        try:
            node.add_message_to_out_buff(message)
        except:
            pass
        pass

    def read_in_buf(self):
        """
        Only returns the input buffer of our TCPServer.

        :return: TCPServer input buffer.
        :rtype: list
        """
        return self._server_in_buf

    def send_messages_to_node(self, node):
        """
        Send buffered messages to the 'node'

        Warnings:
            1. Insert an exception handler here; Maybe the node socket you want to send the message has turned off and
            you need to remove this node from stream nodes.

        :param node:
        :type node Node

        :return:
        """
        try:
            node.send_message()
        except RuntimeError:
            self.remove_node(node)
        except ValueError:
            # FIXME might wanna do sth
            print("Sth Went Wrong")
            pass
        pass

    def send_out_buf_messages(self, only_register=False):
        """
        In this function, we will send whole out buffers to their own clients.

        :return:
        """
        problematic_nodes = []
        if only_register:
            for node in self.nodes:
                try:
                    if node.is_register:
                        self.send_messages_to_node(node)
                except ConnectionResetError:
                    # print("A Node seems to be out of reach: " + str(node.get_server_address()))
                    problematic_nodes.append(node)

        else:
            for node in self.nodes:
                try:
                    self.send_messages_to_node(node)
                except ConnectionResetError:
                    # print("A Node seems to be out of reach: " + str(node.get_server_address()))
                    problematic_nodes.append(node)
        return problematic_nodes
        pass
