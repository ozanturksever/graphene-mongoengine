# from django.db import models
# from django.utils.encoding import force_text
from collections import namedtuple

from graphene import (ID, Boolean, Dynamic, Enum, Field, Float, Int, List,
                      NonNull, String)
from graphene.relay import is_node
from graphene.types.datetime import DateTime
from graphene.types.json import JSONString
from graphene.types.scalars import Scalar
from graphene.utils.str_converters import to_const
from graphql import assert_valid_name
from graphql.language.ast import StringValue

import mongoengine

# from .compat import (ArrayField, HStoreField, JSONField, RangeField,
#                      RelatedObject, UUIDField, DurationField)
# from .fields import get_connection_field, DjangoListField
# from .utils import get_related_model, import_single_dispatch
# from src.common import models
import six
from .utils import import_single_dispatch

singledispatch = import_single_dispatch()
ConversionResult = namedtuple('ConversionResult', ['name', 'field'])


# def convert_choice_name(name):
#     name = to_const(force_text(name))
#     try:
#         assert_valid_name(name)
#     except AssertionError:
#         name = "A_%s" % name
#     return name
#
#
# def get_choices(choices):
#     for value, db_field in choices:
#         if isinstance(db_field, (tuple, list)):
#             for choice in get_choices(db_field):
#                 yield choice
#         else:
#             name = convert_choice_name(value)
#             description = db_field
#             yield name, value, description


def convert_mongoengine_field_with_choices(field, registry=None):
    # choices = getattr(field, 'choices', None)
    # if choices:
    #     meta = field.model._meta
    #     name = '{}{}'.format(meta.object_name, field.name.capitalize())
    #     choices = list(get_choices(choices))
    #     named_choices = [(c[0], c[1]) for c in choices]
    #     named_choices_descriptions = {c[0]: c[2] for c in choices}
    #
    #     class EnumWithDescriptionsType(object):
    #
    #         @property
    #         def description(self):
    #             return named_choices_descriptions[self.name]
    #
    #     enum = Enum(name, list(named_choices), type=EnumWithDescriptionsType)
    #     return enum(description=field.db_field, required=not field.null)
    return convert_mongoengine_field(field, registry)


@singledispatch
def convert_mongoengine_field(field, registry=None):
    raise Exception(
        "Don't know how to convert the MongoEngine field %s (%s)" %
        (field, field.__class__))


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None):
    return String(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None):
    return ID(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.IntField)
def convert_field_to_int(field, registry=None):
    return Int(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return NonNull(Boolean, description=field.db_field)


# @convert_django_field.register(models.NullBooleanField)
# def convert_field_to_nullboolean(field, registry=None):
#     return Boolean(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DecimalField)
@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None):
    return Float(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_date_to_string(field, registry=None):
    return DateTime(description=field.db_field, required=not field.null)


class NdbKeyReferenceField(Scalar):
    # def __init__(self, ndb_key_prop, graphql_type, *args, **kwargs):
    #     self.__ndb_key_prop = ndb_key_prop
    #     self.__graphql_type = graphql_type
    #
    #     _type = self.__graphql_type
    #
    #     super(NdbKeyReferenceField, self).__init__(_type, *args, **kwargs)
    #
    # def resolve_key_reference(self, entity, args, context, info):
    #     print 'resolve'
    #     return None
    #
    # def get_resolver(self, parent_resolver):
    #     return self.resolve_key_reference
    @staticmethod
    def coerce_string(value):
        return six.text_type('%s:%s' % (value.__class__.__name__, value.id))

    serialize = coerce_string


@convert_mongoengine_field.register(mongoengine.ReferenceField)
def convert_field_to_string(field, registry=None):
    model = field.document_type

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        # We do this for a bug in Django 1.8, where null attr
        # is not available in the OneToOneRel instance
        null = getattr(field, 'null', True)
        return Field(_type, required=not null)

    return Dynamic(dynamic_type)


# @convert_django_field.register(models.OneToOneRel)
# def convert_onetoone_field_to_djangomodel(field, registry=None):
#     model = get_related_model(field)
#
#     def dynamic_type():
#         _type = registry.get_type_for_model(model)
#         if not _type:
#             return
#
#         # We do this for a bug in Django 1.8, where null attr
#         # is not available in the OneToOneRel instance
#         null = getattr(field, 'null', True)
#         return Field(_type, required=not null)
#
#     return Dynamic(dynamic_type)
#
#
# @convert_django_field.register(models.ManyToManyField)
# @convert_django_field.register(models.ManyToManyRel)
# @convert_django_field.register(models.ManyToOneRel)
# def convert_field_to_list_or_connection(field, registry=None):
#     model = get_related_model(field)
#
#     def dynamic_type():
#         _type = registry.get_type_for_model(model)
#         if not _type:
#             return
#
#         if is_node(_type):
#             return get_connection_field(_type)
#
#         return DjangoListField(_type)
#
#     return Dynamic(dynamic_type)
#
#
# # For Django 1.6
# @convert_django_field.register(RelatedObject)
# def convert_relatedfield_to_djangomodel(field, registry=None):
#     model = field.model
#
#     def dynamic_type():
#         _type = registry.get_type_for_model(model)
#         if not _type:
#             return
#
#         if isinstance(field.field, models.OneToOneField):
#             return Field(_type)
#
#         if is_node(_type):
#             return get_connection_field(_type)
#         return DjangoListField(_type)
#
#     return Dynamic(dynamic_type)
#
#
# @convert_django_field.register(models.OneToOneField)
# @convert_django_field.register(models.ForeignKey)
# def convert_field_to_djangomodel(field, registry=None):
#     model = get_related_model(field)
#
#     def dynamic_type():
#         _type = registry.get_type_for_model(model)
#         if not _type:
#             return
#
#         return Field(_type, description=field.db_field, required=not field.null)
#
#     return Dynamic(dynamic_type)
#
#
@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_date_to_string(field, registry=None):
    return DateTime(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.ListField)
def convert_postgres_array_to_list(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
    if isinstance(base_type, (Dynamic)):
        base_type = base_type.get_type()._type
    if not isinstance(base_type, (List, NonNull)):
        base_type = type(base_type)
    return List(base_type, description=field.db_field, required=not field.null)

#
#
# @convert_django_field.register(HStoreField)
# @convert_django_field.register(JSONField)
# def convert_posgres_field_to_string(field, registry=None):
#     return JSONString(description=field.db_field, required=not field.null)
#
#
# @convert_django_field.register(RangeField)
# def convert_posgres_range_to_string(field, registry=None):
#     inner_type = convert_django_field(field.base_field)
#     if not isinstance(inner_type, (List, NonNull)):
#         inner_type = type(inner_type)
#     return List(inner_type, description=field.db_field, required=not field.null)
