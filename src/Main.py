from src.Peer import Peer
#
# if __name__ == "__main__":
#     server = Peer("127.0.0.1", 10000, is_root=True)
#     server.run()
#
#     # client = Peer("127.0.0.1", 10001, is_root=False, root_address=("127.0.0.1", 10000))
# print("RUNNINGNNGNGNNGNG")

peer_type = str(input("Input type: "))
if peer_type[0] == 'S':
    server = Peer("127.0.0.1", 10000, is_root=True)
else:
    port = int(input("Input Port: "))
    client = Peer("127.0.0.1", port, is_root=False, root_address=("127.0.0.1", 10000))