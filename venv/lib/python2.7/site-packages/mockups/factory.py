from mockups import generators
from django.db import models


DEFAULT_FIELDCLASS_TO_GENERATOR = (
    (models.BooleanField, generators.BooleanGenerator),
    (models.DateField, generators.DateGenerator),
    (models.DateTimeField, generators.DateTimeGenerator),
    (models.EmailField, generators.EmailGenerator),
    (models.IntegerField, generators.IntegerGenerator),
    (models.IPAddressField, generators.IPAddressGenerator),
    (models.NullBooleanField, generators.NullBooleanGenerator),
    (models.PositiveIntegerField, generators.PositiveIntegerGenerator),
    (models.PositiveSmallIntegerField, generators.PositiveSmallIntegerGenerator),
    (models.SlugField, generators.SlugGenerator),
    (models.SmallIntegerField, generators.SmallIntegerGenerator),
    (models.TextField, generators.LoremGenerator),
    (models.TimeField, generators.TimeGenerator),
    (models.URLField, generators.URLGenerator),
    # field generators
    (models.CharField, generators.CharFieldGenerator),
    (models.DecimalField, generators.DecimalFieldGenerator),
    (models.FilePathField, generators.FilePathFieldGenerator),
    (models.ForeignKey, generators.ForeignKeyFieldGenerator),
    (models.OneToOneField, generators.OneToOneFieldGenerator),
    (models.ManyToManyField, generators.ManyToManyFieldGenerator),
)


class FactoryException(Exception):
    pass


class FactoryMetaClass(type):
    def __new__(cls, name, bases, attrs):
        fieldname_to_generator = {}
        for base in bases[::-1]:
            if hasattr(base, 'fieldname_to_generator'):
                fieldname_to_generator.update(base.fieldname_to_generator)
        for k, v in attrs.items():
            try:
                if issubclass(v, generators.Generator):
                    fieldname_to_generator[k] = attrs.pop(k)
            except TypeError:
                pass
            if isinstance(v, generators.Generator):
                fieldname_to_generator[k] = attrs.pop(k)
        attrs['fieldname_to_generator'] = fieldname_to_generator
        sup = super(FactoryMetaClass, cls)
        return sup.__new__(cls, name, bases, attrs)


class Factory(object):
    """
    Factory class for handing back the correct generator

    values in fieldclass_to_generator and fieldname_to_generator can be
    either of:
    1. A Generator class that does not require arguments
    2. A FieldGenerator class
    3. A Generator instance
    """

    __metaclass__ = FactoryMetaClass

    fieldclass_to_generator = dict(DEFAULT_FIELDCLASS_TO_GENERATOR)
    fieldname_to_generator = {}

    def __init__(self, fieldname_to_generator=None, fieldclass_to_generator=None):
        if fieldname_to_generator is not None:
            self.fieldname_to_generator.update(fieldname_to_generator)
        if fieldclass_to_generator is not None:
            self.fieldclass_to_generator.update(fieldclass_to_generator)
        if hasattr(models, 'BigIntegerField') and \
                models.BigIntegerField not in self.fieldclass_to_generator:
            self.fieldclass_to_generator.update({
                models.BigIntegerField: generators.BigIntegerFieldGenerator
            })

    def get_generator(self, field, **kwargs):
        # fieldname mapping has presidence
        if field.name in self.fieldname_to_generator:
            obj = self.fieldname_to_generator[field.name]
        elif field.choices:
            return generators.ChoiceFieldGenerator(field)
        elif field.default is not models.NOT_PROVIDED:
            return None # bail out
        elif field.__class__ in self.fieldclass_to_generator:
            obj = self.fieldclass_to_generator.get(field.__class__)
        else:
            return None # No matching generator found

        # get the generator instance from obj
        try:
            if issubclass(obj, generators.FieldGenerator):
                return obj(field, **kwargs)
            if issubclass(obj, generators.Generator):
                return obj()
        except TypeError:
            pass
        if isinstance(obj, generators.Generator):
            return obj
        raise FactoryException(u'Invalid generator returned for '
                u'field `%s`: %s' % (field.name, obj))

