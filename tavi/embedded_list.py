"""Provides custom collection class."""
import collections
from tavi.base.document import BaseDocument
from tavi.document import EmbeddedDocument
from tavi.errors import TaffyTypeError

class EmbeddedList(collections.MutableSequence):
    """A custom list for embedded documents. Ensures that only
    EmbeddedDocuments can be added to the list. Supports all the of standard
    list functions, excluding sorting.

    """
    def __init__(self, name):
        self.list_ = list()
        self.name  = name
        self._owner = None

    def __len__(self):
        return len(self.list_)

    def __getitem__(self, index):
        return self.list_[index]

    def __delitem__(self, index):
        del self.list_[index]

    def __repr__(self):
        return str(self.list_)

    def __setitem__(self, index, value):
        self.list_[index] = value

    def __eq__(self, other):
        return self.list_ == other

    @property
    def owner(self):
        """The object that owns this list."""
        return self._owner

    @owner.setter
    def owner(self, value):
        """Sets the owner of the list. Raises a TaffyTypeError if *value* does
        not inherit from tavi.base.document.BaseDocument.

        """
        if not isinstance(value, BaseDocument):
            raise TaffyTypeError(
                "owner must be of type or inherit from "
                "tavi.base.document.BaseDocument"
            )

        self._owner = value

    def find(self, item):
        """Finds *item* in the list and returns it. If not found, returns
        None.

        """
        return next((i for i in self.list_ if i == item), None)

    def insert(self, index, value):
        """Adds *value* to list at *index*. Ensures that *value* is a
        tavi.document.EmbeddedDocument and raises a TaffyTypeError if it is
        not. Checks that *value* is valid before being added. If *value* is not
        valid it adds the errors to the list owner.

        """
        if not isinstance(value, EmbeddedDocument):
            raise TaffyTypeError(
                "tavi.EmbeddedList only accepts "
                "tavi.document.EmbeddedDocument objects"
            )

        if value.valid:
            value.owner = self.owner
            self.list_.insert(index, value)
        else:
            for msg in value.errors.full_messages:
                self.owner.errors.add("%s Error:" % self.name, msg)
