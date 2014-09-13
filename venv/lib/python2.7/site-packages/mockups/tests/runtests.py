#!/usr/bin/env python
from os.path import abspath, dirname, join as pjoin
from os import pardir
import sys
from django.conf import settings


TEST_ROOT = abspath(dirname(__file__))


if not settings.configured:
    settings.configure(
        TEST_ROOT = TEST_ROOT,
        DATABASE_ENGINE = 'sqlite3',
        DATABASE_NAME = pjoin(TEST_ROOT, 'test.sqlite'),
        MEDIA_URL = '/media/',
        MEDIA_ROOT = pjoin(TEST_ROOT, 'media'),
        STATIC_URL = '/static/',
        ADMIN_MEDIA_PREFIX = '/static/admin/',
        STATIC_ROOT = pjoin(TEST_ROOT, 'static'),
        ROOT_URLCONF = 'mockups.tests.urls',
        TEMPLATE_DIRS = (
            pjoin(TEST_ROOT, 'templates'),
        ),
        INSTALLED_APPS = [
            'mockups',
            'mockups.tests',
            'mockups.tests.generator_test',
            'mockups.tests.mockups_test',
            'mockups.tests.sample_app',
        ],
    )

from django.test.simple import run_tests


def runtests(*test_labels):
    test_labels = test_labels or [
        'mockups',
        'generator_test',
        'mockups_test',
    ]
    sys.path.insert(0, pjoin(TEST_ROOT, pardir, pardir))
    failures = run_tests(test_labels , verbosity=1, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])

