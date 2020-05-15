# coding: utf8


class MessageFormatter(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def format_key_path(self, key_path):
        return '-'.join(key_path)

    def format_keys(self, keys):
        return ", ".join(keys)

    def format_fields(self, fields):
        return '-'.join(fields)

    def format_enums(self, enums):
        return '[%s]' % ', '.join(['"%s"' % x for x in enums])

    def format_range(self, min_value, max_value):
        return '[%s, %s]' % (min_value, max_value)

    def one_of_keys_error(self, fields):
        return "more than one of keys `%s` exist" % self.format_keys(fields)

    def none_of_keys_error(self, fields):
        return "none of keys `%s` exists" % self.format_keys(fields)

    def deduction_error(self, src, dest, should_exist):
        if should_exist:
            return "field `%s` must exist when field `%s` exists" % (dest, src)
        else:
            return "field `%s` shouldn't exist when field `%s` exists" % (dest, src)

    def list_length_error(self, min_size, max_size):
        return "invalid list size, valid size is %s" % self.format_range(min_size, max_size)

    def invalid_enums(self, enums):
        return "invalid enum value, valid enums are %s" % self.format_enums(enums)

    def invalid_range(self, min_value, max_value):
        return 'invalid value range, must be in %s' % self.format_range(min_value, max_value)

    def key_not_found(self):
        return 'key not found: %s' % self.format_fields(self.ctx.field_names)

    def field_type_error(self):
        return 'incorrect type for field: %s' % self.format_fields(self.ctx.field_names)

    # i18n names
    @property
    def field_inames(self):
        return self.format_fields(self.ctx.field_names)
