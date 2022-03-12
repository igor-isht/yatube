from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse
from posts.models import Post, Group, Follow


User = get_user_model()
AUTHOR = 'аuthor'
USERNAME = 'MyName'
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
        cls.group = Group.objects.create(
            title='Тестовая группа №2',
            slug=SECOND_GROUP_URL,
            description='Вторая группа'
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Тест подписок для авторизованного пользователя
    def test_subscriptions_for_authorized_client(self):
        follower = User.objects.create_user(username=USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(follower)
        # Подписка
        subscriptions_count = Follow.objects.count()
        # Подписываемся на автора
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.post.author}))
        # Объект Follow существует
        self.assertTrue(
            Follow.objects.filter(
                user=follower,
                author=self.user
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), subscriptions_count + 1)
        # Проверка отображения поста в тестах ниже

        # Отписка
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.post.author}))
        cache.clear()
        self.authorized_client.get(reverse('posts:follow_index'))
        self.assertFalse(
            Follow.objects.filter(
                user=follower,
                author=self.user
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), subscriptions_count)
        # пост более не отображается на follow
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    # Отображение постов у подписчиков/других пользователей
    def test_new_post_appear_on_follow_page(self):
        # Пост отображается у подписчиков
        follower = User.objects.create_user(username=USERNAME)
        self.authorized_client.force_login(follower)
        Follow.objects.create(
                user=follower,
                author=self.user
            )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'])
        # Пост не отображается у неподписчиков
        follower2 = User.objects.create_user(username='YourName')
        self.authorized_client.force_login(follower2)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])
