# coding: utf8

import re
import json


class TypeHolder(object):
    UnknownType = 'UNKNOWN'

    def __init__(self):
        self.integer = False
        self.bool = False
        self.string = False
        self.float = False
        self.dict = False
        self.none = False
        self.dict_data = dict()
        self.list = False
        self.list_item_type = None

    def to_thrift_type(self):
        combo = (self.integer, self.bool, self.string, self.float, self.dict, self.list, self.none)
        s = sum(combo)
        if s == 0:
            return TypeHolder.UnknownType
        if s == 1:
            if self.integer:
                return 'int'
            if self.bool:
                return 'bool'
            if self.string:
                return 'string'
            if self.float:
                return 'double'
            if self.none:
                return 'ERROR'
            if self.dict:
                rep = dict()
                for k, v in self.dict_data.iteritems():
                    rep[k] = v.to_thrift_type()
                return rep
            if self.list:
                item_type = self.list_item_type.to_thrift_type()
                if item_type == TypeHolder.UnknownType:
                    return 'list<UNKNOWN>'
                return 'list<%s>' % item_type
            raise Exception("impossible branch")
        if s == 2:
            if self.integer and self.float:  # 聚合为float
                return 9.99
        return 'Multi(%s)' % str(combo)

    def to_repr(self):
        combo = (self.integer, self.bool, self.string, self.float, self.dict, self.list, self.none)
        s = sum(combo)
        if s == 0:
            return TypeHolder.UnknownType
        if s == 1:
            if self.integer:
                return 999
            if self.bool:
                return True
            if self.string:
                return 'STRING'
            if self.float:
                return 9.99
            if self.none:
                return None
            if self.dict:
                rep = dict()
                for k, v in self.dict_data.iteritems():
                    rep[k] = v.to_repr()
                return rep
            if self.list:
                item_type = self.list_item_type.to_repr()
                if item_type == TypeHolder.UnknownType:
                    return []
                return [item_type]
            raise Exception("impossible branch")
        if s == 2:
            if self.integer and self.float:  # 聚合为float
                return 9.99
        return 'Multi(%s)' % str(combo)


class StructureParser(object):
    def __init__(self):
        self.structure = TypeHolder()

    def to_repr(self):
        return self.structure.to_repr()

    def to_thrift_type(self):
        return self.structure.to_thrift_type()

    def parse(self, data):
        self._parse(data, self.structure)

    def _parse(self, input_data, type_holder):
        if input_data is None:
            type_holder.none = True
        elif isinstance(input_data, int):
            type_holder.integer = True
        elif isinstance(input_data, bool):
            type_holder.bool = True
        elif isinstance(input_data, float):
            type_holder.float = True
        elif isinstance(input_data, basestring):
            type_holder.string = True
        elif isinstance(input_data, dict):
            type_holder.dict = True
            for k, v in input_data.iteritems():
                holder = type_holder.dict_data.get(k)
                if not holder:
                    holder = TypeHolder()
                    type_holder.dict_data[k] = holder
                self._parse(v, holder)
        elif isinstance(input_data, list):
            type_holder.list = True
            if not type_holder.list_item_type:
                type_holder.list_item_type = TypeHolder()
            for item in input_data:
                self._parse(item, type_holder.list_item_type)
        else:
            raise Exception("unsupported input-data type: %s", type(input_data))


js = dict(a=1, b=2, c='ABC')
parser = StructureParser()
parser.parse(js)
print parser.to_repr()
