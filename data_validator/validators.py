# coding: utf8

from .core import *


# validator
def range(min_value, max_value):
    def __wrapper__(ctx):
        if ctx.value < min_value or ctx.value > max_value:
            raise MessageException(ctx.formatter.invalid_range(ctx, min_value, max_value))
    return __wrapper__


def enums(values):
    def __wrapper__(ctx):
        if ctx.value not in values:
            raise MessageException(ctx.formatter.invalid_enums(ctx, values))
    return __wrapper__
