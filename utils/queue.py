from task_manager import task_queue


class Queue:
    """
    Represents a First-In-First-Out (FIFO) queue used within the simulation system.

    This class manages the queuing of items (e.g., patients) in a specific section or ward
    of the simulation. It ensures that items are processed in the order they arrive,
    maintaining the integrity and realism of the simulation's operational flow.

    Attributes:
        name (str): The name of the queue (e.g., "emergency", "icu").
        state (SystemState): Reference to the current system state, used to access the simulation time.
        _queue (list): Internal list to store queued items along with their insertion index for stability.
        _index (int): Counter to maintain the order of insertion, ensuring FIFO behavior even with identical items.
    """

    def __init__(self, name, state):
        """
        Initializes the Queue with a specified name and system state.

        Args:
            name (str): The name of the queue.
            state (SystemState): The current state of the system, providing context for the queue.
        """
        self.name = name
        self.state = state
        self._queue = []  # Internal list to hold the elements as tuples (index, item)
        self._index = 0  # To maintain insertion order for stability

    def push(self, item):
        """
        Adds an item to the end of the queue.

        This method appends the item to the internal queue along with a unique index to ensure
        that the order of insertion is preserved, even if multiple items are identical.
        After adding the item, it updates the task queue to reflect the new size of the queue.

        Args:
            item (Any): The item to be added to the queue.
        """
        # Append the item with the current index for maintaining order
        self._queue.append((self._index, item))
        self._index += 1  # Increment the index for the next insertion

        # Notify analytics of the queue size change
        task_queue.append(
            {
                "task": "queue",
                "queue": self.name,
                "time": self.state.current_time,
                "size": len(self._queue)
            }
        )

    def pop(self):
        """
        Removes and returns the first item from the queue.

        This method follows the FIFO principle by removing the item that was inserted first.
        It also updates the task queue to reflect the new size of the queue after popping.
        If the queue is empty, it raises an IndexError.

        Returns:
            Any: The item that was removed from the front of the queue.

        Raises:
            IndexError: If attempting to pop from an empty queue.
        """
        if self._queue:
            # Notify analytics of the queue size change before popping
            task_queue.append(
                {
                    "task": "queue",
                    "queue": self.name,
                    "time": self.state.current_time,
                    "size": len(self._queue) - 1  # Size after popping
                }
            )
            return self._queue.pop(0)[1]  # Remove and return the first item's value
        raise IndexError("pop from an empty queue")

    def peek(self):
        """
        Returns the first item in the queue without removing it.

        This method allows inspection of the next item to be processed without altering the queue's state.

        Returns:
            Any: The first item in the queue if it exists; otherwise, None.
        """
        if self._queue:
            return self._queue[0][1]  # Return the first item's value without removing it
        return None  # Return None if the queue is empty

    def is_empty(self):
        """
        Checks whether the queue is empty.

        Returns:
            bool: True if the queue has no items; False otherwise.
        """
        return len(self._queue) == 0

    def __len__(self):
        """
        Returns the number of items currently in the queue.

        Enables the use of the `len()` function on Queue instances.

        Returns:
            int: The number of items in the queue.
        """
        return len(self._queue)

    def __repr__(self):
        """
        Provides a string representation of the queue for debugging purposes.

        Returns:
            str: A string showing the queue's name and the number of items it contains.
        """
        return f"Queue(name={self.name}, size={len(self)})"
