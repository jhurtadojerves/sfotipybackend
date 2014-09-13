# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import related
from mockups import constraints, generators, signals, factory
from mockups.helpers import get_mockup


class IGNORE_FIELD(object):
    pass


class CreateInstanceError(Exception):
    pass


class Link(object):
    '''
    Handles logic of following or generating foreignkeys and m2m relations.
    '''
    def __init__(self, fields=None, default=None):
        self.fields = {}
        self.subfields = {}
        self.default = default

        fields = fields or {}
        if fields is True:
            fields = {'ALL': None}
        if not isinstance(fields, dict):
            fields = dict([(v, None) for v in fields])
        for field, value in fields.items():
            try:
                fieldname, subfield = field.split('__', 1)
                self.subfields.setdefault(fieldname, {})[subfield] = value
            except ValueError:
                self.fields[field] = value

    def __getitem__(self, key):
        return self.fields.get(key,
            self.fields.get('ALL', self.default))

    def __iter__(self):
        for field in self.fields:
            yield field
        for key, value in self.subfields.items():
            yield '%s__%s' % (key, value)

    def __contains__(self, value):
        if 'ALL' in self.fields:
            return True
        if value in self.fields:
            return True
        return False

    def get_deep_links(self, field):
        if 'ALL' in self.fields:
            fields = {'ALL': self.fields['ALL']}
        else:
            fields = self.subfields.get(field, {})
            if 'ALL' in fields:
                fields = {'ALL': fields['ALL']}
        return Link(fields, default=self.default)


class Mockup(object):
    '''
    .. We don't support the following fields yet:

        * ``XMLField``
        * ``FileField``
        * ``ImageField``

        Patches are welcome.
    '''

    follow_fk = True
    generate_fk = False
    follow_m2m = {'ALL': (1,5)}
    generate_m2m = False
    creation_tries = 1000
    default_constraints = [ constraints.unique_constraint,
            constraints.unique_together_constraint]
    factory = factory.Factory

    def __init__(self, model, constraints=None, follow_fk=None,
            generate_fk=None, follow_m2m=None, generate_m2m=None,
            factory=None):
        '''
        Parameters:
            ``model``: A model class which is used to create the test data.

            ``constraints``: A list of callables. The constraints are used to
            verify if the created model instance may be used. The callable
            gets the actual model as first and the instance as second
            parameter. The instance is not populated yet at this moment.  The
            callable may raise an :exc:`InvalidConstraint` exception to
            indicate which fields violate the constraint.

            ``follow_fk``: A boolean value indicating if foreign keys should be
            set to random, already existing, instances of the related model.

            ``generate_fk``: A boolean which indicates if related models should
            also be created with random values. The *follow_fk* parameter will
            be ignored if *generate_fk* is set to ``True``.

            ``follow_m2m``: A tuple containing minium and maximum of model
            instances that are assigned to ``ManyToManyField``. No new
            instances will be created. Default is (1, 5).  You can ignore
            ``ManyToManyField`` fields by setting this parameter to ``False``.

            ``generate_m2m``: A tuple containing minimum and maximum number of
            model instance that are newly created and assigned to the
            ``ManyToManyField``. Default is ``False`` which disables the
            generation of new related instances. The value of ``follow_m2m``
            will be ignored if this parameter is set.

            ``factory``: A Factory *instance*, overriding the one defined in the
            Mockup class.
        '''
        self.model = model
        self.constraints = constraints or []

        # instantiate the factory class
        if factory is not None:
            self.factory = factory.__class__
            self._factory = factory
        else:
            self._factory = self.factory()

        if follow_fk is not None:
            self.follow_fk = follow_fk
        if not isinstance(self.follow_fk, Link):
            self.follow_fk = Link(self.follow_fk)

        if generate_fk is not None:
            self.generate_fk = generate_fk
        if not isinstance(self.generate_fk, Link):
            self.generate_fk = Link(self.generate_fk)

        if follow_m2m is not None:
            if not isinstance(follow_m2m, dict):
                if follow_m2m:
                    follow_m2m = Link({'ALL': follow_m2m})
                else:
                    follow_m2m = Link(False)
            self.follow_m2m = follow_m2m
        if not isinstance(self.follow_m2m, Link):
            self.follow_m2m = Link(self.follow_m2m)

        if generate_m2m is not None:
            if not isinstance(generate_m2m, dict):
                if generate_m2m:
                    generate_m2m = Link({'ALL': generate_m2m})
                else:
                    generate_m2m = Link(False)
            self.generate_m2m = generate_m2m
        if not isinstance(self.generate_m2m, Link):
            self.generate_m2m = Link(self.generate_m2m)

        for constraint in self.default_constraints:
            self.add_constraint(constraint)

        self._fieldname_to_generator = {}
        self.prepare_class()

    def prepare_class(self):
        '''
        This method is called after the :meth:`__init__` method. It has no
        semantic by default.
        '''
        pass

    def update_fieldname_generator(self, **kwargs):
        '''
        Updates the factory instance with new generators
        '''
        self._factory.fieldname_to_generator.update(kwargs)

    def add_constraint(self, constraint):
        '''
        Add a *constraint* to the mockup.
        '''
        self.constraints.append(constraint)

    def get_generator(self, field):
        '''
        Return a value generator based on the field instance that is passed to
        this method. This function may return ``None`` which means that the
        specified field will be ignored (e.g. if no matching generator was
        found).
        '''

        params = {
            'follow_fk': self.follow_fk,
            'generate_fk': self.generate_fk,
            'follow_m2m': self.follow_m2m,
            'generate_m2m': self.generate_m2m,
        }
        return self._factory.get_generator(field, **params)

    def get_value(self, field):
        '''
        Return a random value that can be assigned to the passed *field*
        instance.
        '''
        if field not in self._fieldname_to_generator:
            self._fieldname_to_generator[field] = self.get_generator(field)
        generator = self._fieldname_to_generator[field]
        if generator is None:
            return IGNORE_FIELD
        return generator.get_value()

    def process_field(self, instance, field):
        value = self.get_value(field)
        if value is not IGNORE_FIELD:
            setattr(instance, field.name, value)

    def process_m2m(self, instance, field):
        # check django's version number to determine how intermediary models
        # are checked if they are auto created or not.
        from django import VERSION
        auto_created_through_model = False
        through = field.rel.through
        if VERSION < (1, 2):
            if through:
                if isinstance(through, basestring):
                    bits = through.split('.')
                    if len(bits) < 2:
                        bits = [instance._meta.app_label] + bits
                    through = models.get_model(*bits)
            else:
                auto_created_through_model = True
        else:
            auto_created_through_model = through._meta.auto_created

        if auto_created_through_model:
            return self.process_field(instance, field)
        # if m2m relation has intermediary model:
        #   * only generate relation if 'generate_m2m' is given
        #   * first generate intermediary model and assign a newly created
        #     related model to the foreignkey
        if field.name in self.generate_m2m:
            # get fk to related model on intermediary model
            related_fks = [fk
                for fk in through._meta.fields
                if isinstance(fk, related.ForeignKey) and \
                    fk.rel.to is field.rel.to]
            self_fks = [fk
                for fk in through._meta.fields
                if isinstance(fk, related.ForeignKey) and \
                    fk.rel.to is self.model]
            assert len(related_fks) == 1
            assert len(self_fks) == 1
            related_fk = related_fks[0]
            self_fk = self_fks[0]
            min_count, max_count = self.generate_m2m[field.name]

            related_mockup = get_mockup(field.rel.to)
            related_generator = generators.InstanceGenerator(related_mockup)
            through_mockup = get_mockup(through)
            # update the through mockup factory
            params = {
                self_fk.name: generators.StaticGenerator(instance),
                related_fk.name: generators.InstanceGenerator(related_mockup),
            }
            through_mockup.update_fieldname_generator(**params)

            generator = generators.MultipleInstanceGenerator(through_mockup,
                    min_count=min_count, max_count=max_count)
            generator.generate()

    def check_constrains(self, instance):
        '''
        Return fieldnames which need recalculation.
        '''
        recalc_fields = []
        for constraint in self.constraints:
            try:
                constraint(self.model, instance)
            except constraints.InvalidConstraint, e:
                recalc_fields.extend(e.fields)
        return recalc_fields

    def post_process_instance(self, instance):
        '''
        Overwrite this method to modify the created *instance* at the last
        possible moment. It gets the generated *instance* and must return the
        modified instance.
        '''
        return instance

    def create_one(self, commit=True):
        '''
        Create and return one model instance. If *commit* is ``False`` the
        instance will not be saved and many to many relations will not be
        processed.

        May raise :exc:`CreateInstanceError` if constraints are not satisfied.
        '''
        creation_tries = self.creation_tries
        instance = self.model()
        process = instance._meta.fields
        while process and creation_tries > 0:
            for field in process:
                self.process_field(instance, field)
            process = self.check_constrains(instance)
            creation_tries -= 1
        if creation_tries == 0:
            raise CreateInstanceError(
                u'Cannot solve constraints for "%s", tried %d times. '
                u'Please check value generators or model constraints. '
                u'At least the following fields are involved: %s' % (
                    '%s.%s' % (
                        self.model._meta.app_label,
                        self.model._meta.object_name),
                    self.creation_tries,
                    ', '.join([field.name for field in process]),
            ))
        if commit:
            instance.save()
            for field in instance._meta.many_to_many:
                self.process_m2m(instance, field)
        signals.instance_created.send(
            sender=self,
            model=self.model,
            instance=instance,
            committed=commit)
        return self.post_process_instance(instance)

    def create(self, count=1, commit=True):
        '''
        Create and return ``count`` model instances. If *commit* is ``False``
        the instances will not be saved and many to many relations will not be
        processed.

        May raise ``CreateInstanceError`` if constraints are not satisfied.

        The method internally calls :meth:`create_one` to generate instances.
        '''
        object_list = []
        for i in xrange(count):
            instance = self.create_one(commit=commit)
            object_list.append(instance)
        return object_list

    def iter(self, count=1, commit=True):
        for i in xrange(count):
            yield self.create_one(commit=commit)

    def __iter__(self):
        yield self.create_one()
