from task_manager import task_queue


class Queue:
    def __init__(self, name, state):
        self.name = name
        self.state = state
        self._queue = []  # Internal list to hold the elements
        self._index = 0  # To maintain insertion order for stability

    def push(self, item):
        # Simply append the item to the queue with an index for stability
        self._queue.append((self._index, item))
        self._index += 1
        task_queue.append(
            {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
        )

    def pop(self):
        # Pop the first inserted item (FIFO order)
        if self._queue:
            task_queue.append(
                {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
            )
            return self._queue.pop(0)[1]
        raise IndexError("pop from an empty queue")

    def peek(self):
        # Peek at the first item without removing it
        if self._queue:
            return self._queue[0][1]
        return None

    def is_empty(self):
        return len(self._queue) == 0

    def __len__(self):
        return len(self._queue)
