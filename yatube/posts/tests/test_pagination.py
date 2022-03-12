from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()
GROUP_URL = 'test_slug'


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_URL,
            description='Тестовое описание',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'Post number {i}',
                group=cls.group,
                author=cls.user,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginators(self):

        templates_page_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': GROUP_URL}),
            reverse('posts:profile', kwargs={'username': self.post.author})
        )

        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
