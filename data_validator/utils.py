# coding: utf8

from . import *
import inspect


class IntegerField(Field):
    def __init__(self, name, *args, **kwargs):
        Field.__init__(self, name, IntegerType, *args, **kwargs)


class StringField(Field):
    def __init__(self, name, *args, **kwargs):
        Field.__init__(self, name, StringType, *args, **kwargs)


class FloatField(Field):
    def __init__(self, name, *args, **kwargs):
        Field.__init__(self, name, FloatType, *args, **kwargs)


class BoolField(Field):
    def __init__(self, name, *args, **kwargs):
        Field.__init__(self, name, BoolType, *args, **kwargs)
