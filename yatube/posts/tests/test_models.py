from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()
AUTHOR = 'аuthor'
GROUP_URL = 'test_slug'
TEST_TITLE = 'Тестовая группа'
TEST_DESCRIPTION = 'Тестовое описание'
TEST_TEXT = 'Тестовый текст'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=GROUP_URL,
            description=TEST_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        post = PostModelTest.post
        object_names = {
            (group.title): str(group),
            (post.text[:15]): str(post),
        }
        for value, expected_value in object_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)
