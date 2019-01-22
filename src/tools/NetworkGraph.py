import time

import collections


class GraphNode:
    def __init__(self, address):
        self.address=address
        self.parent=None
        self.left_child=None
        self.right_child=None
        self.reunion_timer=0
        self.alive=True

        pass

    def set_parent(self, parent):
        self.parent=parent
        pass

    def set_address(self, new_address):
        self.address=new_address
        pass

    def __reset(self):
       #self.address=None
        self.parent=None
        pass

    def add_child(self, child):


        pass

    def number_of_child(self, child):
        cnt=0
        if self.right_child is not None : cnt+=1
        if self.left_child  is not None : cnt+=1
        return cnt





class NetworkGraph:
    def __init__(self, root):
        self.root = root
        root.alive = True

        self.nodes = {root.address:root}

    def find_live_node(self):
        """
        Here we should find a neighbour for the sender.
        Best neighbour is the node who is nearest to the root and has not more than one child.

        Code design suggestion:
            1. Do a BFS algorithm to find the target.

        Warnings:
            1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
               any other nodes in it's sub-tree.

        :param sender: The node address we want to find best neighbour for it.
        :type sender: tuple

        :return: Best neighbour for sender.
        :rtype: GraphNode
        """


        frontier= collections.deque()
        head = self.root

        while(head.number_of_child ==2):
            tmp = frontier.popleft()
            frontier.append( tmp.left_child  )
            frontier.append( tmp.right_child )
            head=frontier.popleft()
            frontier.appendleft(head)

        return head



        pass

    def find_node(self, ip, port):

        return self.nodes.get((ip,port))

        pass

    def turn_on_node(self, node_address):
        self.nodes[node_address].alive = True

        pass

    def turn_off_node(self, node_address):
        self.nodes[node_address].alive = False

        turned_off_node = self.nodes.get(node_address)
        turned_off_node.parent = None



        if turned_off_node.left_child != None:
            self.turn_off_node(turned_off_node.left_child)

        if (turned_off_node.right_child != None):
            self.turn_off_node(turned_off_node.right_child)

        turned_off_node.left_child = None
        turned_off_node.right_child = None

        pass

    def remove_node(self, node_address):

        hazfi=self.nodes.get(node_address)
        hazfi.parent=None
        self.nodes.pop(hazfi.address)

        if(hazfi.left_child!=None):
            self.remove_node(hazfi.left_child)

        if (hazfi.right_child != None):
            self.remove_node(hazfi.right_child)



        pass

    def add_node(self, ip, port, father_address):

        """
        Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

        Warnings:
            1. Don't forget to set the new node as one of the father_address children.
            2. Before using this function make sure that there is a node which has father_address.



        :param ip: IP address of the new node.
        :param port: Port of the new node.
        :param father_address: Father address of the new node

        :type ip: str
        :type port: int
        :type father_address: tuple


        :return:
        """


        new_node=GraphNode((ip,port))
        self.nodes[(ip,port)]=new_node
        new_node.parent=father_address

        if self.nodes[father_address].left_child is not None:
            self.nodes[father_address].left_child =new_node

        else:
            self.nodes[father_address].right_child=new_node






