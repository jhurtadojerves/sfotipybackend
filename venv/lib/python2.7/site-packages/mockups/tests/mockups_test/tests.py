# -*- coding: utf-8 -*-
import mockups
from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase
from mockups import generators
from mockups import Factory
from mockups.base import Mockup, CreateInstanceError,  Link
from mockups_test.models import *


RELATED_MODELS = [ RelatedModel, RelatedModelQ ]

class SimpleFactory(Factory):
    name = generators.StaticGenerator('foo')

class SimpleMockup(Mockup):
    factory = SimpleFactory


class TestBasicModel(TestCase):
    def assertEqualOr(self, first, second, fallback):
        if first != second and not fallback:
            self.fail()

    def test_create(self):
        filler = Mockup(BasicModel)
        filler.create(10)
        self.assertEqual(BasicModel.objects.count(), 10)

    def test_constraints(self):
        filler = Mockup(BasicModel)
        for obj in filler.create(100):
            self.assertTrue(len(obj.chars) > 0)
            self.assertEqual(type(obj.chars), unicode)
            self.assertTrue(len(obj.shortchars) <= 2)
            self.assertEqual(type(obj.shortchars), unicode)
            self.assertTrue(type(obj.blankchars), unicode)
            self.assertEqualOr(type(obj.nullchars), unicode, None)
            self.assertEqual(type(obj.slugfield), unicode)
            self.assertEqual(type(obj.defaultint), int)
            self.assertEqual(obj.defaultint, 1)
            self.assertEqual(type(obj.intfield), int)
            self.assertEqual(type(obj.sintfield), int)
            self.assertEqual(type(obj.pintfield), int)
            self.assertEqual(type(obj.psintfield), int)
            self.assertEqual(type(obj.datefield), date)
            self.assertEqual(type(obj.datetimefield), datetime)
            self.assertEqual(type(obj.defaultdatetime), datetime)
            self.assertEqual(obj.defaultdatetime, y2k())
            self.assertEqual(type(obj.decimalfield), Decimal)
            self.assertTrue('@' in obj.emailfield)
            self.assertTrue('.' in obj.emailfield)
            self.assertTrue(' ' not in obj.emailfield)
            self.assertTrue(obj.ipaddressfield.count('.'), 3)
            self.assertTrue(len(obj.ipaddressfield) >= 7)
        self.assertEqual(BasicModel.objects.count(), 100)

    def test_factory(self):
        int_value = 1
        char_values = (u'a', u'b')
        class GF(Factory):
            intfield = generators.StaticGenerator(1)
            chars = generators.ChoiceGenerator(char_values)
            nullbool = generators.NullBooleanGenerator
            shortchars = generators.CallableGenerator(lambda: u'ab')
        class M(Mockup):
            factory = GF

        filler = M(BasicModel)
        for obj in filler.create(100):
            self.assertEqual(obj.intfield, int_value)
            self.assertTrue(obj.chars in char_values)
            self.assertTrue(obj.nullbool in (False, True, None))
            self.assertEqual(obj.shortchars, u'ab')


class TestRelations(TestCase):
    def test_generate_foreignkeys(self):
        for m in RELATED_MODELS:
            filler = Mockup(
                m,
                generate_fk=True)
            for obj in filler.create(100):
                self.assertEqual(obj.related.__class__, BasicModel)
                self.assertEqual(obj.limitedfk.name, 'foo')

    def test_deep_generate_foreignkeys(self):
        filler = Mockup(
            DeepLinkModel2,
            generate_fk=True)
        for obj in filler.create(10):
            self.assertEqual(obj.related.__class__, DeepLinkModel1)
            self.assertEqual(obj.related.related.__class__, SimpleModel)
            self.assertEqual(obj.related.related2.__class__, SimpleModel)

    def test_deep_generate_foreignkeys2(self):
        filler = Mockup(
            DeepLinkModel2,
            follow_fk=False,
            generate_fk=('related', 'related__related'))
        for obj in filler.create(10):
            self.assertEqual(obj.related.__class__, DeepLinkModel1)
            self.assertEqual(obj.related.related.__class__, SimpleModel)
            self.assertEqual(obj.related.related2, None)

    def test_generate_only_some_foreignkeys(self):
        for m in RELATED_MODELS:
            filler = Mockup(
                m,
                generate_fk=('related',))
            for obj in filler.create(100):
                self.assertEqual(obj.related.__class__, BasicModel)
                self.assertEqual(obj.limitedfk, None)

    def test_follow_foreignkeys(self):
        related = Mockup(BasicModel).create()[0]
        self.assertEqual(BasicModel.objects.count(), 1)

        simple = SimpleModel.objects.create(name='foo')
        simple2 = SimpleModel.objects.create(name='bar')

        for m in RELATED_MODELS:
            filler = Mockup(
                m,
                follow_fk=True)
            for obj in filler.create(100):
                self.assertEqual(obj.related, related)
                self.assertEqual(obj.limitedfk, simple)

    def test_follow_only_some_foreignkeys(self):
        related = Mockup(BasicModel).create()[0]
        self.assertEqual(BasicModel.objects.count(), 1)

        simple = SimpleModel.objects.create(name='foo')
        simple2 = SimpleModel.objects.create(name='bar')

        for m in RELATED_MODELS:
            filler = Mockup(
                m,
                follow_fk=('related',))
            for obj in filler.create(100):
                self.assertEqual(obj.related, related)
                self.assertEqual(obj.limitedfk, None)

    def test_follow_fk_for_o2o(self):
        # OneToOneField is the same as a ForeignKey with unique=True
        filler = Mockup(O2OModel, follow_fk=True)

        simple = SimpleModel.objects.create()
        obj = filler.create()[0]
        self.assertEqual(obj.o2o, simple)

        self.assertRaises(CreateInstanceError, filler.create)

    def test_generate_fk_for_o2o(self):
        # OneToOneField is the same as a ForeignKey with unique=True
        filler = Mockup(O2OModel, generate_fk=True)

        all_o2o = set()
        for obj in filler.create(10):
            all_o2o.add(obj.o2o)

        self.assertEqual(set(SimpleModel.objects.all()), all_o2o)

    def test_follow_m2m(self):
        related = Mockup(SimpleModel).create()[0]
        self.assertEqual(SimpleModel.objects.count(), 1)

        filler = Mockup(
            M2MModel,
            follow_m2m=(2, 10))
        for obj in filler.create(10):
            self.assertEqual(list(obj.m2m.all()), [related])

    def test_follow_only_some_m2m(self):
        related = Mockup(SimpleModel).create()[0]
        self.assertEqual(SimpleModel.objects.count(), 1)
        other_related = Mockup(OtherSimpleModel).create()[0]
        self.assertEqual(OtherSimpleModel.objects.count(), 1)

        filler = Mockup(
            M2MModel,
            follow_m2m={
                'm2m': (2, 10),
            })
        for obj in filler.create(10):
            self.assertEqual(list(obj.m2m.all()), [related])
            self.assertEqual(list(obj.secondm2m.all()), [])

    def test_generate_m2m(self):
        filler = Mockup(
            M2MModel,
            generate_m2m=(1, 5))
        all_m2m = set()
        all_secondm2m = set()
        for obj in filler.create(10):
            self.assertTrue(1 <= obj.m2m.count() <= 5)
            self.assertTrue(1 <= obj.secondm2m.count() <= 5)
            all_m2m.update(obj.m2m.all())
            all_secondm2m.update(obj.secondm2m.all())
        self.assertEqual(SimpleModel.objects.count(), len(all_m2m))
        self.assertEqual(OtherSimpleModel.objects.count(), len(all_secondm2m))

    def test_generate_only_some_m2m(self):
        filler = Mockup(
            M2MModel,
            generate_m2m={
                'm2m': (1, 5),
            })
        all_m2m = set()
        all_secondm2m = set()
        for obj in filler.create(10):
            self.assertTrue(1 <= obj.m2m.count() <= 5)
            self.assertEqual(0, obj.secondm2m.count())
            all_m2m.update(obj.m2m.all())
            all_secondm2m.update(obj.secondm2m.all())
        self.assertEqual(SimpleModel.objects.count(), len(all_m2m))
        self.assertEqual(OtherSimpleModel.objects.count(), len(all_secondm2m))

    def test_generate_m2m_with_intermediary_model(self):
        filler = Mockup(
            M2MModelThrough,
            generate_m2m=(1, 5))
        all_m2m = set()
        for obj in filler.create(10):
            self.assertTrue(1 <= obj.m2m.count() <= 5)
            all_m2m.update(obj.m2m.all())
        self.assertEqual(SimpleModel.objects.count(), len(all_m2m))


class TestUniqueConstraints(TestCase):
    def test_unique_field(self):
        filler = Mockup(UniqueTestModel)
        count = len(filler.model._meta.
            get_field_by_name('choice1')[0].choices)
        for obj in filler.create(count):
            pass

    def test_unique_together(self):
        filler = Mockup(UniqueTogetherTestModel)
        count1 = len(filler.model._meta.
            get_field_by_name('choice1')[0].choices)
        count2 = len(filler.model._meta.
            get_field_by_name('choice2')[0].choices)
        for obj in filler.create(count1 * count2):
            pass


class TestGenerators(TestCase):
    def test_instance_selector(self):
        Mockup(SimpleModel).create(10)

        result = generators.InstanceSelector(SimpleModel).generate()
        self.assertEqual(result.__class__, SimpleModel)

        for i in xrange(10):
            result = generators.InstanceSelector(
                SimpleModel, max_count=10).generate()
            self.assertTrue(0 <= len(result) <= 10)
            for obj in result:
                self.assertEqual(obj.__class__, SimpleModel)
        for i in xrange(10):
            result = generators.InstanceSelector(
                SimpleModel, min_count=5, max_count=10).generate()
            self.assertTrue(5 <= len(result) <= 10)
            for obj in result:
                self.assertEqual(obj.__class__, SimpleModel)
        for i in xrange(10):
            result = generators.InstanceSelector(
                SimpleModel, min_count=20, max_count=100).generate()
            # cannot return more instances than available
            self.assertEqual(len(result), 10)
            for obj in result:
                self.assertEqual(obj.__class__, SimpleModel)

        # works also with queryset as argument
        result = generators.InstanceSelector(SimpleModel.objects.all()).generate()
        self.assertEqual(result.__class__, SimpleModel)


class TestLinkClass(TestCase):
    def test_flat_link(self):
        link = Link(('foo', 'bar'))
        self.assertTrue('foo' in link)
        self.assertTrue('bar' in link)
        self.assertFalse('spam' in link)

        self.assertEqual(link['foo'], None)
        self.assertEqual(link['spam'], None)

    def test_nested_links(self):
        link = Link(('foo', 'foo__bar', 'spam__ALL'))
        self.assertTrue('foo' in link)
        self.assertFalse('spam' in link)
        self.assertFalse('egg' in link)

        foolink = link.get_deep_links('foo')
        self.assertTrue('bar' in foolink)
        self.assertFalse('egg' in foolink)

        spamlink = link.get_deep_links('spam')
        self.assertTrue('bar' in spamlink)
        self.assertTrue('egg' in spamlink)

    def test_links_with_value(self):
        link = Link({'foo': 1, 'spam__egg': 2}, default=0)
        self.assertTrue('foo' in link)
        self.assertEqual(link['foo'], 1)
        self.assertFalse('spam' in link)
        self.assertEqual(link['spam'], 0)

        spamlink = link.get_deep_links('spam')
        self.assertTrue('egg' in spamlink)
        self.assertEqual(spamlink['bar'], 0)
        self.assertEqual(spamlink['egg'], 2)

    def test_always_true_link(self):
        link = Link(True)
        self.assertTrue('field' in link)
        self.assertTrue('any' in link)

        link = link.get_deep_links('field')
        self.assertTrue('field' in link)
        self.assertTrue('any' in link)

        link = Link(('ALL',))
        self.assertTrue('field' in link)
        self.assertTrue('any' in link)

        link = link.get_deep_links('field')
        self.assertTrue('field' in link)
        self.assertTrue('any' in link)

    def test_inherit_always_true_value(self):
        link = Link({'ALL': 1})
        self.assertEqual(link['foo'], 1)

        sublink = link.get_deep_links('foo')
        self.assertEqual(sublink['bar'], 1)


class TestRegistry(TestCase):
    def setUp(self):
        self.original_registry = mockups.helpers._registry
        mockups.helpers._registry = {}

    def tearDown(self):
        mockups.helpers._registry = self.original_registry

    def test_registration(self):
        mockups.register(SimpleModel, SimpleMockup)
        self.assertTrue(SimpleModel in mockups.helpers._registry)
        self.assertEqual(mockups.helpers._registry[SimpleModel], SimpleMockup)

    def test_create(self):
        mockups.register(SimpleModel, SimpleMockup)
        for obj in mockups.create(SimpleModel, 10):
            self.assertEqual(obj.name, 'foo')
        obj = mockups.create_one(SimpleModel)
        self.assertEqual(obj.name, 'foo')

    def test_inheritance(self):
        class A(Factory):
            x = generators.StaticGenerator
        class B(A):
            pass
        a = A()
        b = B()
        self.assertEqual(a.fieldname_to_generator, b.fieldname_to_generator)

    def test_overwrite_attributes(self):
        class GF(Factory):
            name = generators.StaticGenerator('bar')
        class M(SimpleMockup):
            factory = GF
        mockups.register(SimpleModel, M)
        for obj in mockups.create(SimpleModel, 10):
            self.assertEqual(obj.name, 'bar')
        obj = mockups.create_one(SimpleModel)
        self.assertEqual(obj.name, 'bar')


class TestMockupAPI(TestCase):
    def setUp(self):
        self.original_registry = mockups.helpers._registry
        mockups.helpers._registry = {}

    def tearDown(self):
        mockups.helpers._registry = self.original_registry


class TestManagementCommand(TestCase):
    def setUp(self):
        from mockups.management.commands.mockups import Command
        self.command = Command()
        self.options = {
            'no_follow_fk': None,
            'no_follow_m2m': None,
            'generate_fk': None,
            'follow_m2m': None,
            'generate_m2m': None,
            'verbosity': '0',
            'use': '',
        }
        self.original_registry = mockups.helpers._registry
        mockups.helpers._registry = {}

    def tearDown(self):
        mockups.helpers._registry = self.original_registry

    def test_basic(self):
        models = ()
        # empty attributes are allowed
        self.command.handle(*models, **self.options)
        self.assertEqual(SimpleModel.objects.count(), 0)

        models = ('mockups_test.SimpleModel:1',)
        self.command.handle(*models, **self.options)
        self.assertEqual(SimpleModel.objects.count(), 1)

        models = ('mockups_test.SimpleModel:5',)
        self.command.handle(*models, **self.options)
        self.assertEqual(SimpleModel.objects.count(), 6)

    def test_generate_fk(self):
        models = ('mockups_test.DeepLinkModel2:1',)
        self.options['generate_fk'] = 'related,related__related'
        self.command.handle(*models, **self.options)
        obj = DeepLinkModel2.objects.get()
        self.assertTrue(obj.related)
        self.assertTrue(obj.related.related)
        self.assertEqual(obj.related.related2, obj.related.related)

    def test_generate_fk_with_no_follow(self):
        models = ('mockups_test.DeepLinkModel2:1',)
        self.options['generate_fk'] = 'related,related__related'
        self.options['no_follow_fk'] = True
        self.command.handle(*models, **self.options)
        obj = DeepLinkModel2.objects.get()
        self.assertTrue(obj.related)
        self.assertTrue(obj.related.related)
        self.assertEqual(obj.related.related2, None)

    def test_generate_fk_with_ALL(self):
        models = ('mockups_test.DeepLinkModel2:1',)
        self.options['generate_fk'] = 'ALL'
        self.command.handle(*models, **self.options)
        obj = DeepLinkModel2.objects.get()
        self.assertTrue(obj.related)
        self.assertTrue(obj.related.related)
        self.assertTrue(obj.related.related2)
        self.assertTrue(obj.related.related != obj.related.related2)

    def test_no_follow_m2m(self):
        Mockup(SimpleModel).create(1)

        models = ('mockups_test.NullableFKModel:1',)
        self.options['no_follow_m2m'] = True
        self.command.handle(*models, **self.options)
        obj = NullableFKModel.objects.get()
        self.assertEqual(obj.m2m.count(), 0)

    def test_follow_m2m(self):
        Mockup(SimpleModel).create(10)
        Mockup(OtherSimpleModel).create(10)

        models = ('mockups_test.M2MModel:25',)
        self.options['follow_m2m'] = 'm2m:3:3,secondm2m:0:10'
        self.command.handle(*models, **self.options)

        for obj in M2MModel.objects.all():
            self.assertEqual(obj.m2m.count(), 3)
            self.assertTrue(0 <= obj.secondm2m.count() <= 10)

    def test_generate_m2m(self):
        models = ('mockups_test.M2MModel:10',)
        self.options['generate_m2m'] = 'm2m:1:1,secondm2m:2:5'
        self.command.handle(*models, **self.options)

        all_m2m, all_secondm2m = set(), set()
        for obj in M2MModel.objects.all():
            self.assertEqual(obj.m2m.count(), 1)
            self.assertTrue(
                2 <= obj.secondm2m.count() <= 5 or
                obj.secondm2m.count() == 0)
            all_m2m.update(obj.m2m.all())
            all_secondm2m.update(obj.secondm2m.all())
        self.assertEqual(all_m2m, set(SimpleModel.objects.all()))
        self.assertEqual(all_secondm2m, set(OtherSimpleModel.objects.all()))

    def test_using_registry(self):
        mockups.register(SimpleModel, SimpleMockup)
        models = ('mockups_test.SimpleModel:10',)
        self.command.handle(*models, **self.options)
        for obj in SimpleModel.objects.all():
            self.assertEqual(obj.name, 'foo')

