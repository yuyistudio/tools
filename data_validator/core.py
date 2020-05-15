# coding: utf8


from .exceptions import *
from .formatter import MessageFormatter
import inspect
import math
import logging


def _check_fns(fns):
    for fn in fns:
        if not inspect.isfunction(fn):
            raise ConfigException("invalid All() parameter, function expected, got `%s`", type(fn))


def All(*fns):
    _check_fns(fns)
    def __wrapper__(ctx):
        for fn in fns:
            fn(ctx)
    return __wrapper__


def Any(*fns):
    _check_fns(fns)
    def __wrapper__(ctx):
        last_exception = None
        for fn in fns:
            try:
                fn(ctx)
                return  # its ok
            except BaseException, e:
                last_exception = e
                continue
        raise last_exception
    return __wrapper__


class FieldNode(object):
    def __init__(self, key, value, field_config):
        self.key = key
        self.value = value
        self.field_config = field_config


class Context(object):
    def __init__(self, schema, input_data):
        if not isinstance(input_data, dict) and not isinstance(input_data, list):
            raise ValidationException("invalid input data %s" % type(input_data))
        self.input_data = input_data  # the whole data to validate.
        self.root_schema = schema  # currently-executing root schema
        self.formatter = None  # MessageFormatter
        self.user_data = None
        node = FieldNode(None, input_data, schema)
        self.nodes = [node]

    def push(self, key, field_config):
        logging.info("pushing key `%s`", key)
        data = self.nodes[-1].value
        if isinstance(data, dict):
            value = data.get(key)
        else:
            value = data[key]  # list
        logging.info("pushing value `%s`", value)
        node = FieldNode(key, value, field_config)
        self.nodes.append(node)

    def pop(self):
        logging.info("poping key `%s`", self.nodes[-1].key)
        self.nodes.pop()

    # currently validating schema
    @property
    def schema(self):
        for i in range(len(self.nodes) - 1, 0, -1):
            conf = self.nodes[i].field_config
            if issubclass(type(conf), Schema):
                return conf

    # container data of type dict of list.
    @property
    def data(self):
        logging.info("nodes count %d", len(self.nodes))
        if len(self.nodes) == 1:
            return self.nodes[0].value
        return self.nodes[-2].value

    @property
    def field_configs(self):
        return [x.field_config for x in self.nodes if x]

    @property
    def field_config(self):
        return self.nodes[-1].field_config

    @property
    def field_key(self):
        return self.nodes[-1].key

    @property
    def key_path(self):
        return [x.key for x in self.nodes if x.key]

    @property
    def field_data(self):
        return self.value

    @property
    def value(self):
        res = self.nodes[-1].value
        # logging.info("getting data `%s`", res)
        return res

    @property
    def field_names(self):
        return [x._name for x in self.field_configs if x and x._name]

    @property
    def current_schema(self):
        return self.field_config

    @property
    def field_inames(self):
        return self.formatter.format_fields(self.field_names)


class BaseValidator(object):
    def __init__(self):
        self.field_config = None

    def validate(self, ctx):
        raise ValidationException("not implement")


class EmptyValidator(object):
    def validate(self, ctx):
        pass


class StrValidator(BaseValidator):
    def validate(self, ctx):
        logging.info("checking for str: %s %s", ctx.value, type(ctx.value))
        if not isinstance(ctx.value, basestring):
            raise FieldTypeException()


class FloatValidator(BaseValidator):
    def validate(self, ctx):
        if not isinstance(ctx.value, float):
            raise FieldTypeException()


class IntValidator(BaseValidator):
    def validate(self, ctx):
        if not isinstance(ctx.value, int):
            raise FieldTypeException()


class BoolValidator(BaseValidator):
    def validate(self, ctx):
        if not isinstance(ctx.value, bool):
            raise FieldTypeException()


class DictValidator(BaseValidator):
    def validate(self, ctx):
        if not isinstance(ctx.value, dict):
            raise FieldTypeException()


class ListValidator(BaseValidator):
    def validate(self, ctx):
        if not isinstance(ctx.value, list):
            raise FieldTypeException()


StringType = StrValidator()
FloatType = FloatValidator()
IntegerType = IntValidator()
BoolType = BoolValidator()
DictType = DictValidator()
ListType = ListValidator()
AnyType = EmptyValidator()


class OneOfFieldValidator(BaseValidator):
    def __init__(self, *field_keys):
        BaseValidator.__init__(self)
        self.field_keys = field_keys

    def validate(self, ctx):
        count = 0
        for key in self.field_keys:
            if key in ctx.data:
                count += 1
        if count == 1:
            return  # fine
        if count == 0:
            print ctx.data, self.field_keys
            raise MessageException(ctx.formatter.none_of_keys_error(ctx, self.field_keys))
        raise MessageException(ctx.formatter.one_of_keys_error(ctx, self.field_keys))


class AtLeastValidator(BaseValidator):
    def __init__(self, min_field_count, *field_keys):
        BaseValidator.__init__(self)
        if min_field_count <= 0:
            raise ConfigException("invalid min_field_count, should be positive integer")
        self.field_keys = field_keys
        self.min_field_count = min_field_count

    def validate(self, ctx):
        count = 0
        for key in self.field_keys:
            if key in ctx.data:
                count += 1
        if count < self.min_field_count:
            raise MessageException(ctx.formatter.none_of_keys_error(ctx, self.field_keys))


class DeductionValidator(BaseValidator):
    def __init__(self, src, src_cond, dest, dest_should_exist):
        BaseValidator.__init__(self)
        assert isinstance(src, basestring)
        assert isinstance(dest, basestring)
        self.src = src
        self.src_cond = src_cond
        self.dest = dest
        self.dest_should_exist = dest_should_exist

    def validate(self, ctx):
        if self.src in ctx.data:
            if self.src_cond and not self.src_cond(ctx.data[self.src]):
                return
            print ctx.data[self.src], self.src
            if (self.dest in ctx.data) != self.dest_should_exist:
               raise MessageException(ctx.formatter.deduction_error(ctx, self.src, self.dest, self.dest_should_exist))


class BaseField(object):
    def __init__(self, name, field_type, required=True, cond=None, validator=None, value_validator=None):
        """
        A base class for primitive field, list field, and dict field(aka object field).
        Field class contains all constraints for the field itself.
        :param name: display name for end-users.
        :param field_type: instance of the subclass of BaseValidator
        :param required: bool
        :param cond: function(value) bool
        :param validator: function(context)
        :return:
        """
        self._type_validator = None
        self._required = True
        self._cond = cond  # if self._conf() returns False, skip the validation of the schema which contains this field.
        self._name = name
        self._value_validator = value_validator

        # field type
        assert field_type
        if issubclass(type(field_type), BaseValidator):
            self._type_validator = field_type
        else:
            raise ConfigException("invalid type parameter `%s`" % field_type)

        # validator
        self._validator = None
        if validator is None:
            pass
        elif inspect.isfunction(validator):
            self._validator = All(validator)
        elif issubclass(type(validator), BaseValidator):
            self._validator = validator
        else:
            raise ConfigException("invalid validator `%s`" % validator)

    def check_cond(self, value):
        return not self._cond or self._cond(value)

    # for subclass
    def check(self, ctx):
        pass

    def pre_check(self, ctx):
        """
        :param ctx:
        :param value:
        :return: stop following validations by returning True.
        """
        pass

    def validate(self, ctx):
        if ctx.field_config:
            logging.info("checking %s %s", ctx.field_config._name, ctx.value)
        self.pre_check(ctx)
        self._type_validator.validate(ctx)
        self._validator and self._validator(ctx)
        self._value_validator and self._value_validator(ctx.value)
        self.check(ctx)


class Field(BaseField):
    pass


class ListField(BaseField):
    def __init__(self, name, required=True, cond=None, validator=None, min_length=0, max_length=0, fixed_fields=None, field=None, value_validator=None):
        """
        JSON List
        :param name: display name for end-users.
        :param min_length:
        :param max_length:
        :param fixed_fields: specify the types of each list item, eg. [str, int, int]
        :param field: type of list item.
        :return:
        """
        BaseField.__init__(self, name, ListType, required=required, cond=cond, validator=validator, value_validator=value_validator)
        if fixed_fields and field:
            raise ConfigException("only one parameter of [fixed_fields, field] can be set")
        self._min_length = min_length
        self._max_length = max_length
        self._fixed_fields = fixed_fields
        self._field = field

        # fixed fields
        if self._fixed_fields is not None:
            if not self._fixed_fields:
                raise ConfigException("invalid fixed fields")
            for f in self._fixed_fields:
                if not issubclass(type(f), BaseField):
                    raise ConfigException("invalid fixed fields, item is not subclass of BaseField")

    def validate(self, ctx):
        BaseField.validate(self, ctx)
        if self._min_length and len(ctx.value) < self._min_length:
            raise MessageException(ctx.formatter.list_length_error(self._min_length, self._max_length))
        if self._max_length and len(ctx.value) > self._max_length:
            raise MessageException(ctx.formatter.list_length_error(self._min_length, self._max_length))

        # check each field
        if self._fixed_fields:
            array = ctx.field_data
            if len(array) != len(self._fixed_fields):
                raise MessageException(ctx.formatter.list_length_error(len(self._fixed_fields), len(self._fixed_fields)))
            for idx in range(len(array)):
                ctx.push(idx, self._fixed_fields[idx])
                self._fixed_fields[idx].validate(ctx)
                ctx.pop()

        # check field
        if self._field:
            array = ctx.field_data
            for idx in range(len(array)):
                ctx.push(idx, self._field)
                self._field.validate(ctx)
                ctx.pop()


class Schema(BaseField):
    def __init__(self, name=None):
        """
        Json Dict.
        :param name: schema name for end-users.
        :return:
        """
        BaseField.__init__(self, name, DictType)
        self._validators = list()
        self._fields = list()
        self._not_required = set()
        self._key2field_config = dict()
        for field_key in dir(self):
            if field_key.startswith('_'):
                continue
            field_conf = getattr(self, field_key)
            if not isinstance(field_conf, BaseField) and not issubclass(type(field_conf), BaseField):
                print 'ignored:', field_key, " conf:", field_conf
                continue
            self._fields.append((field_key, field_conf))
            self._key2field_config[field_key] = field_conf
        if not self._fields:
            raise ConfigException("empty fields not allowed")
        self.on_init()

    def on_init(self):
        pass

    def _iter_fields(self, ctx):
        for field_key, field_conf in self._fields:
            ctx.push(field_key, field_conf)
            yield field_key, field_conf
            ctx.pop()

    def not_required(self, *field_keys):
        self._not_required.update(field_keys)

    def get_field_config(self, field_key):
        if field_key not in self._key2field_config:
            raise ConfigException("field not in schema:`%s`" % field_key)
        return self._key2field_config[field_key]

    def validate(self, ctx):
        assert ctx.data
        BaseField.validate(self, ctx)

        # check required
        for field_key, field_conf in self._iter_fields(ctx):
            # logging.info("validating field: %s", field_key)
            # required
            if field_key not in self._not_required and field_conf._required and field_key not in ctx.data:
                logging.info("not required %s, data %s", self._not_required, ctx.data)
                raise KeyNotFoundException(ctx.key_path)

        # check cond. if any False, return false
        for field_key, field_conf in self._iter_fields(ctx):
            value = ctx.data.get(field_key)
            if value:
                if not field_conf.check_cond(value):
                    raise IgnoredSchemaException()

        # check values
        for field_key, field_conf in self._iter_fields(ctx):
            if field_key not in ctx.data:
                continue
            field_conf.validate(ctx)

        # check validators
        for validator in self._validators:
            validator.validate(ctx)

        self.check(ctx)

    def add_validator(self, *validators):
        self._validators.extend(validators)

    def _check_fields(self, field_keys):
        for field_key in field_keys:
            if not hasattr(self, field_key):
                raise ConfigException('non-existing require_one_of() field `%s`' % field_key)

    def _mark_not_required(self, field_keys):
        self._not_required.update(field_keys)

    def only_one_of(self, *field_keys):
        self._check_fields(field_keys)
        self._mark_not_required(field_keys)
        self._validators.append(OneOfFieldValidator(*field_keys))

    def at_least_one(self, *field_keys):
        self.at_least(1, *field_keys)

    def at_least(self, min_field_count, *field_keys):
        """
        at least one field exists
        :param field_keys: list of string
        :return:
        """
        if not isinstance(min_field_count, int):
            raise ConfigException("min_field_count should be of type Integer")
        self._check_fields(field_keys)
        self._mark_not_required(field_keys)
        self._validators.append(AtLeastValidator(1, *field_keys))

    def reverse_deduce(self, source_field_key, source_cond, *dest_field_keys):
        """
        if source condition satisfied, dest fields shouldn't exist.
        :param source_field_key: string
        :param source_cond: None, or [function(value) bool]
        :param dest_field: string
        :return:
        """
        for dest_field_key in dest_field_keys:
            self._validators.append(DeductionValidator(source_field_key, source_cond, dest_field_key, False))

    def deduce(self, source_field_key, source_cond, *dest_field_keys):
        """
         dest fields must exist if source condition satisfied.
        :param source_field_key: string
        :param source_cond: None, or [function(value) bool]
        :param dest_field: string
        :return:
        """
        for dest_field_key in dest_field_keys:
            self._validators.append(DeductionValidator(source_field_key, source_cond, dest_field_key, True))


# the global formatter class.
_default_formatter_cls = MessageFormatter


# overwrite the global formatter class for localization.
def set_default_formatter(formatter_cls):
    assert formatter_cls
    global _default_formatter_cls
    _default_formatter_cls = formatter_cls


class BaseSchemaValidator(object):
    def __init__(self, *schema_types):
        """
        :param schema_types: list of schema type. schema-type must be of the subclass of Schema.
        :return:
        """
        if not schema_types:
            raise ConfigException("empty schemas")
        self.schemas = None
        self.schema_types = schema_types
        self.formatter_cls = None
        self.formatter = None
        self.ctx = None

    def __call__(self, *args, **kwargs):
        instance = type(self)(*self.schema_types)
        instance.schemas = [x() for x in self.schema_types]
        instance.formatter_cls = self.formatter_cls
        return instance

    def validate(self, data, user_data=None):
        """
        validate an JSON object.
        :param data: instance of list to validate
        :param user_data: any data that will be held in Context, for any purpose.
        :return:
        """
        if not self.schemas:
            raise ValidationException("schema not usable, create an instance with Schema at first.")
        self.ctx = Context(None, data)
        self.ctx.user_data = user_data
        self.formatter = (self.formatter_cls or _default_formatter_cls)(self.ctx)
        self.ctx.formatter = self.formatter
        self.formatter.ctx = self.ctx
        try:
            self._validate(data, user_data)
        except KeyNotFoundException as e:
            logging.exception(e)
            not_found_key = str(e)
            self.ctx.push(not_found_key, self.ctx.schema.get_field_config(not_found_key))
            logging.info("field names %s", self.ctx.field_names)
            raise MessageException(self.formatter.key_not_found())
        except FieldTypeException as e:
            logging.exception(e)
            raise MessageException(self.formatter.field_type_error())

    def _validate(self, data, user_data):
        for schema in self.schemas:
            self.ctx = Context(schema, data)
            self.ctx.formatter = self.formatter
            self.formatter.ctx = self.ctx
            self.ctx.user_data = user_data
            try:
                schema.validate(self.ctx)
            except StopValidation:
                continue

    def set_formatter_class(self, formatter_cls):
        """
        set formatter class for this validator, independent of the global one.
        :param formatter_cls: subclass of class MessageFormatter
        :return:
        """
        self.formatter_cls = formatter_cls
