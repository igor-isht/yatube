from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse
from posts.models import Post, Group, User

USERNAME = 'MyName'
AUTHOR = 'аuthor'
GROUP_URL = 'test_slug'
SECOND_GROUP_URL = 'test_slug_2'
TEST_TITLE = 'Тестовая группа'
TEST_DESCRIPTION = 'Тестовое описание'
TEST_TEXT = 'Тестовый текст'


class PostsPagesTests(TestCase):
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
            text=TEST_TEXT,
            group=cls.group,
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username=USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        # Загружаем страницу
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        # Удаляем пост
        posts_count = Post.objects.count()
        Post.objects.filter(text=TEST_TEXT, pk=posts_count).delete()
        # Смотрим, изменилась ли страница
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(content, response.content)
        # Очистка кэша, запрос и сравнение
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(content, response.content)
