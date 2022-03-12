from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()
USERNAME = 'MyName'
AUTHOR = 'аuthor'
GROUP_URL = 'test_slug'
# В проекте может появиться такая страница с таким же адресом,
# поэтому адрес для тестов лучше задать тут
UNEXPECTING_PAGE = 'unexisting_page'
TEST_TITLE = 'Тестовая группа'
TEST_DESCRIPTION = 'Тестовое описание'
TEST_TEXT = 'Тестовый текст'


class PostURLTests(TestCase):
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
        self.guest_client = Client()
        self.user = User.objects.create_user(username=USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверка общедоступных страниц
    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_list_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/group/{GROUP_URL}/')
        self.assertEqual(response.status_code, 200)

    def test_profile_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/profile/{USERNAME}/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/posts/{PostURLTests.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_unexisting_page_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/{UNEXPECTING_PAGE}/')
        self.assertEqual(response.status_code, 404)

    # Проверка доступности для авторизованного пользователя
    def test_create_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    # Проверка доступности для автора
    def test_post_edit_url_exists_at_desired_location(self):
        self.user = User.objects.get(username=AUTHOR)
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        self.user = User.objects.get(username=AUTHOR)
        self.authorized_client.force_login(self.user)
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{GROUP_URL}/': 'posts/group_list.html',
            f'/profile/{USERNAME}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
