import queue

class EventBus:
    """
    The EventBus is a queue-based mechanism for handling events.
    It takes events from various components and dispatches them
    to registered handlers.
    """
    def __init__(self):
        self._events = queue.Queue()

    def put(self, event):
        """
        Puts a new event into the queue.
        """
        self._events.put(event)

    def get(self):
        """
        Gets an event from the queue.
        """
        return self._events.get()

    def empty(self):
        """
        Checks if the queue is empty.
        """
        return self._events.empty()
