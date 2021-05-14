import queue
import socket
import os

class PollableQueue(queue.Queue):
    """Speacial Message Queue for tasks which need to block/wait on socket input and a classic message queue
        The task can use a selector to register its listening sockets and this queue which has internal sockets
        to trigger the selector of the task.
    """
    def __init__(self, task_name, logger):
        super().__init__()

        self.task_name = task_name
        self.name = task_name + "_queue"
        self.logger = logger

        # Create a pair of connected sockets
        if os.name == 'posix':
            self._putsocket, self._getsocket = socket.socketpair()
        else:
            # Compatibility on non-POSIX systems
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._putsocket.connect(server.getsockname())
            self._getsocket, _ = server.accept()
            server.close()

    def fileno(self):
        """ This function returns the fileno of the get-socket.
        This is used by a Selector to register socket events
        """
        return self._getsocket.fileno()

    def get_msg(self, blocking=True):
        """ Get a message from the queue
        @param blocking: not used in this queue type. Included for compatibility of interface
        @return: return message queue item
         """
        self.logger.info("%s: %s takes from queue and blocks", self.name, self.task_name)
        self._getsocket.recv(1)
        msg = super().get()
        self.logger.info("%s: %s got item from queue and releases ", self.name, self.task_name)

        return msg

    def send_msg(self, msg, sender_name):
        """ Add a new message in the queue
        @param msg: message to send
        @param sender_name: name of the sending task
        @return:
        """

        self.logger.info("%s: %s adds item to queue: %s", self.name, sender_name, msg.message)
        super().put(msg)
        self._putsocket.send(b'x')  # could by any other character
        self.logger.info("%s: %s added item to queue", self.name, sender_name)

