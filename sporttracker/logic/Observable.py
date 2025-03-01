from abc import ABC, abstractmethod


class Listener(ABC):
    @abstractmethod
    def on_update(self) -> None:
        pass


class Observable(ABC):
    def __init__(self) -> None:
        self._listeners: set[Listener] = set()

    def add_listener(self, listener: Listener) -> None:
        self._listeners.add(listener)

    def remove_listener(self, listener: Listener) -> None:
        self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener.on_update()
