"""
The NamedIdManager class provides access to a collection of NamedIdObjects
"""

from abc import abstractmethod


class NamedIdObject:
    @property
    @abstractmethod
    def id_(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class NamedIdManager():
    """Provides access to a collection of NamedIdObject"""

    def __init__(self, objects: list[NamedIdObject], id_length: int = 10) -> None:
        self._id_length = id_length
        if min([len(obj.id_) for obj in objects]) > id_length:
            raise Exception("Id length violation (InstanceManager failed to initialize)")

        self._objects = {obj.id_: obj for obj in objects}
        self._choices = [(obj.id_,  obj.name) for obj in objects]

    @property
    def id_length(self) -> int:
        return self._id_length

    @property
    def choices(self) -> list[tuple[str, str]]:
        """Lists all available instances as tuple (id, name)"""
        return self._choices

    def get(self, id_: str) -> NamedIdObject:
        """Returns the instance by id"""
        return self._objects[id_]
