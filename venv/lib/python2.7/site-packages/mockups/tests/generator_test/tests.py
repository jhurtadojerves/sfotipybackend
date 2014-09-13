import os
from django.conf import settings
from django.test import TestCase
from mockups import generators


class FilePathTests(TestCase):
    def test_media_path_generator(self):
        generator = generators.MediaFilePathGenerator(recursive=True)
        for i in range(10):
            path = generator.get_value()
            self.assertTrue(len(path) > 0)
            self.assertFalse(path.startswith('/'))
            media_path = os.path.join(settings.MEDIA_ROOT, path)
            self.assertTrue(os.path.exists(media_path))
            self.assertTrue(os.path.isfile(media_path))

    def test_media_path_generator_in_subdirectory(self):
        generator = generators.MediaFilePathGenerator(path='textfiles')
        for i in range(10):
            path = generator.get_value()
            self.assertTrue(path.startswith('textfiles/'))
            self.assertTrue(path.endswith('.txt'))

