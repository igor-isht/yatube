import shutil
import tempfile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group, Comment

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
class PostCreateFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username=USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
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
        self.form_data_create = {
            'text': 'Тестовый текст2',
            'group': 1,
            'image': uploaded,
        }
        self.form_data_edit = {
            'text': 'Новый текст',
            'group': 2,
        }
        self.posts_count = Post.objects.count()

    # Создание поста авторизованным пользователем
    def test_post_was_created_by_autorized_client(self):
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data_create,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': USERNAME}))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                group=1,
                image='posts/small.gif',
                pk=self.posts_count + 1,
            ).exists()
        )
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertEqual(response.status_code, 200)

    # Создание поста неавторизованным пользователем
    def test_post_was_not_created_by_guest_client(self):
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data_create,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/')
        self.assertNotIn('Тестовый текст2', reverse('posts:index'))
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertEqual(response.status_code, 200)

    # Редактирование автором
    def test_post_was_edited_by_author(self):
        self.user = User.objects.get(username=AUTHOR)
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title=TEST_TITLE,
            slug=SECOND_GROUP_URL,
            description=TEST_DESCRIPTION,
        )
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': self.post.id}),
            data=self.form_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'pk': self.post.id}))
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(
            Post.objects.filter(
                pk=self.post.id,
                text='Новый текст',
                group='2',
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    # Редактирование авторизованным пользователем
    def test_post_was_not_edited_by_autorized_client(self):
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': self.post.id}),
            data=self.form_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'pk': self.post.id}))
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(
            Post.objects.filter(
                pk=self.post.id,
                text=TEST_TEXT,
                group='1',
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    # Редактирование анонимом
    def test_post_was_not_edited_by_guest_client(self):
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'pk': self.post.id}),
            data=self.form_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'pk': self.post.id}))
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(
            Post.objects.filter(
                pk=self.post.id,
                text=TEST_TEXT,
                group='1',
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    # Комментарий от авторизованного пользователя
    def test_comment_was_sended_by_authorized_client(self):
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'pk': self.post.id}),
            data={'text': 'Текст комментария(тест)'},
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'pk': self.post.id}))
        self.assertTrue(
            Comment.objects.filter(
                text='Текст комментария(тест)',
                pk=comment_count + 1,
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response.status_code, 200)

    # Комментарий от анонима
    def test_comment_was_not_sended_by_guest_client(self):
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'pk': self.post.id}),
            data={'text': 'Текст комментария(тест)'},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/')
        self.assertFalse(
            Comment.objects.filter(
                text='Текст комментария(тест)',
                pk=comment_count,
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response.status_code, 200)
