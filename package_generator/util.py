# coding: utf8


import cPickle as pickle

def _get_fields(obj):
    return [v for v in obj.__dict__ if not v.startswith('__')]


_fields_key = 'storage_fields'


def dump(obj):
    if hasattr(obj, _fields_key):
        fields = getattr(obj, _fields_key)
    else:
        fields = _get_fields(obj)

    if isinstance(fields, basestring):
        fields = fields.split()

    data = dict()
    for field in fields:
        v = getattr(obj, field)
        if not is_inner_type(v):
            v = dump(v)
        data[field] = v

    return data


def load(obj, data):
    if hasattr(obj, _fields_key):
        fields = getattr(obj, _fields_key)
    else:
        fields = _get_fields(obj)

    if isinstance(fields, basestring):
        fields = fields.split()

    for field in fields:
        if field not in data:
            continue

        ori_v = getattr(obj, field)
        if ori_v is None:
            raise Exception("unknown type for obj(%s) field(%s)" % (type(obj), field))

        vt = type(ori_v)
        if vt is dict:
            pass  # todo
        elif vt == list:
            pass  # todo
        elif is_inner_type(ori_v):
            setattr(obj, field, data[field])
        else:
            load(ori_v, data[field])


def is_inner_type(obj):
    return type(obj) in (int, float, bool, str, unicode)


filename = '.pickle.dump'


def save_to_disk(obj):
    fout = open(filename, 'w')
    pickle.dump(obj, fout)
    fout.close()


def load_from_dist():
    return pickle.load(open(filename))
