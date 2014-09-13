# -*- coding: utf-8 -*-
import mockups
from datetime import datetime
from django.contrib.auth.models import User, UNUSABLE_PASSWORD
from mockups import Mockup, Factory
from mockups import generators


class UserFactory(Factory):
    username = generators.UUIDGenerator(max_length=30)
    first_name = generators.LoremWordGenerator(1)
    last_name = generators.LoremWordGenerator(1)
    password = generators.StaticGenerator(UNUSABLE_PASSWORD)
    is_active = generators.StaticGenerator(True)
    # don't generate admin users
    is_staff = generators.StaticGenerator(False)
    is_superuser = generators.StaticGenerator(False)
    date_joined = generators.DateTimeGenerator(max_date=datetime.now())
    last_login = generators.DateTimeGenerator(max_date=datetime.now())


class UserMockup(Mockup):
    '''
    :class:`UserMockup` is automatically used by default to create new
    ``User`` instances. It uses the following values to assure that you can
    use the generated instances without any modification:

    * ``username`` only contains chars that are allowed by django's auth forms.
    * ``email`` is unique.
    * ``first_name`` and ``last_name`` are single, random words of the lorem
      ipsum text.
    * ``is_staff`` and ``is_superuser`` are always ``False``.
    * ``is_active`` is always ``True``.
    * ``date_joined`` and ``last_login`` are always in the past and it is
      assured that ``date_joined`` will be lower than ``last_login``.
    '''

    # don't follow permissions and groups
    follow_m2m = False
    factory = UserFactory

    def __init__(self, *args, **kwargs):
        '''
        By default the password is set to an unusable value, this makes it
        impossible to login with the generated users. If you want to use for
        example ``mockups.create_one('auth.User')`` in your unittests to have
        a user instance which you can use to login with the testing client you
        can provide a ``username`` and a ``password`` argument. Then you can do
        something like::

            mockups.create_one('auth.User', username='foo', password='bar`)
            self.client.login(username='foo', password='bar')
        '''
        self.username = kwargs.pop('username', None)
        self.password = kwargs.pop('password', None)
        super(UserMockup, self).__init__(*args, **kwargs)
        if self.username:
            self.update_fieldname_generator(
                username = generators.StaticGenerator(self.username)
                )

    def unique_email(self, model, instance):
        if User.objects.filter(email=instance.email):
            raise mockups.InvalidConstraint(('email',))

    def prepare_class(self):
        self.add_constraint(self.unique_email)

    def post_process_instance(self, instance):
        # make sure user's last login was not before he joined
        if instance.last_login < instance.date_joined:
            instance.last_login = instance.date_joined
        if self.password:
            instance.set_password(self.password)
        return instance


mockups.register(User, UserMockup, fail_silently=True)
