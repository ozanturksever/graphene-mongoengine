from collections import OrderedDict

import six

from graphene import Field, ObjectType
from graphene.types.objecttype import ObjectTypeMeta
from graphene.types.options import Options
from graphene.types.utils import merge, yank_fields_from_attrs
from graphene.utils.is_base_type import is_base_type

from .converter import convert_mongoengine_field_with_choices
from .registry import Registry, get_global_registry
from .utils import (get_model_fields, is_valid_mongoengine_model)


def construct_fields(options):
    _model_fields = get_model_fields(options.model)
    only_fields = options.only_fields
    exclude_fields = options.exclude_fields

    fields = OrderedDict()
    for field in _model_fields:
        name = field.name
        is_not_in_only = only_fields and name not in options.only_fields
        is_already_created = name in options.fields
        is_excluded = name in exclude_fields or is_already_created
        if is_not_in_only or is_excluded:
            # We skip this field if we specify only_fields and is not
            # in there. Or when we exclude this field in exclude_fields
            continue
        converted = convert_mongoengine_field_with_choices(field, options.registry)
        if not converted:
            continue
        fields[name] = converted

    return fields


class MongoengineObjectTypeMeta(ObjectTypeMeta):
    @staticmethod
    def __new__(cls, name, bases, attrs):
        # Also ensure initialization is only performed for subclasses of
        # DjangoObjectType
        if not is_base_type(bases, MongoengineObjectTypeMeta):
            return type.__new__(cls, name, bases, attrs)

        defaults = dict(
            name=name,
            description=attrs.pop('__doc__', None),
            model=None,
            local_fields=None,
            only_fields=(),
            exclude_fields=(),
            interfaces=(),
            registry=None
        )

        options = Options(
            attrs.pop('Meta', None),
            **defaults
        )
        if not options.registry:
            options.registry = get_global_registry()
        assert isinstance(options.registry, Registry), (
            'The attribute registry in {}.Meta needs to be an instance of '
            'Registry, received "{}".'
        ).format(name, options.registry)
        assert is_valid_mongoengine_model(options.model), (
            'You need to pass a valid MongoEngine Document in {}.Meta, received "{}".'
        ).format(name, options.model)

        cls = ObjectTypeMeta.__new__(cls, name, bases, dict(attrs, _meta=options))

        options.registry.register(cls)
        options.mongoengine_fields = yank_fields_from_attrs(
            construct_fields(options),
            _as=Field,
        )
        options.fields = merge(
            options.interface_fields,
            options.mongoengine_fields,
            options.base_fields,
            options.local_fields
        )

        return cls


class MongoengineObjectType(six.with_metaclass(MongoengineObjectTypeMeta, ObjectType)):
    def resolve_id(self, args, context, info):
        return str(self.id)

    # @classmethod
    # def is_type_of(cls, root, context, info):
    #     if isinstance(root, cls):
    #         return True
    #     if not is_valid_mongoengine_model(type(root)):
    #         raise Exception((
    #                             'Received incompatible instance "{}".'
    #                         ).format(root))
    #     print 'model', root._meta, cls
    #     # model = root._meta.model
    #     model = root
    #     print 'model', model
    #     return model == cls._meta.model
    #
    def fill(self, data):
        for key, field in self._meta.model._fields.iteritems():
            if key in data:
                setattr(self, key, data[key])

    @classmethod
    def get_node(cls, id, context, info):
        try:
            return cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            return None

