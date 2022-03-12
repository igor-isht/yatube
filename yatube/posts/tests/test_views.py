import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from posts.models import Post, Group


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'MyName'
AUTHOR = 'аuthor'
GROUP_URL = 'test_slug'
SECOND_GROUP_URL = 'test_slug_2'
TEST_TITLE = 'Тестовая группа'
TEST_DESCRIPTION = 'Тестовое описание'
TEST_TEXT = 'Тестовый текст'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR)
        small_gif = (
                    b'\x47\x49\x46\x38\x39\x61\x02\x00'
                    b'\x01\x00\x80\x00\x00\x00\x00\x00'
                    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                    b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=GROUP_URL,
            description=TEST_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            text=TEST_TEXT,
            group=cls.group,
            author=cls.user,
            image=uploaded,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа №2',
            slug=SECOND_GROUP_URL,
            description='Вторая группа'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверка использования правильных шаблонов
    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': GROUP_URL}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'pk': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'pk': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка использования контекстов
    def test_pages_show_correct_context(self):
        templates_page_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': GROUP_URL}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        )
        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_obj = response.context['page_obj'][0]
                post_text = post_obj.text

                self.assertEqual(post_text, TEST_TEXT)
                post_author = post_obj.author
                self.assertEqual(post_author, self.post.author)
                post_group = post_obj.group
                self.assertEqual(post_group, self.post.group)
                post_img = post_obj.image
                self.assertEqual(post_img, self.post.image)

    # тест изображения в пост дитейл
    def test_post_detail_contain_image(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'pk': self.post.id}))
        post_obj = response.context['post']
        post_img = post_obj.image
        self.assertEqual(post_img, self.post.image)

    # Post_detail содержит один пост
    def test_post_detail_page_list_is_1(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'pk': self.post.id}))
        self.assertEqual(response.context['post_obj'].count(), 1)

    # проверка полей создания поста
    def test_create_posts_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # проверка редактирования поста по id
    def test_edit_posts_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'pk': self.post.id}))
        post_obj = response.context['post']
        self.assertEqual(post_obj, self.post)

    # Пост попал на нужные страницы
    def test_post_exist_in_desired_pages(self):
        # Пост отображается на желаемых страницах
        templates_page_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': GROUP_URL}),
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_obj = response.context['page_obj']
                self.assertIn(self.post, post_obj)
        # Пост не отображается страницах других групп
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': SECOND_GROUP_URL}))
        post_obj = response.context['page_obj']
        self.assertNotIn(self.post, post_obj)

    # Тест кэширования
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
