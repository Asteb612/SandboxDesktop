#!/usr/bin/env python3
# -*- coding: utf-8 -*

class EventHander:
    pass

class ResourceManager(object):
    """."""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_resources'):
            cls._resources = super(ResourceManager, cls).__new__(cls, *args, **kwargs)
        return cls._resources

    def __init__(self):
        """."""
        self._events = EventHander()

    @property
    def events(self):
        return self._events
