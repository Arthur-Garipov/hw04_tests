from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            description='Тестовый заголовок',
            title='Тестовый титл',
            slug='test-slug',
        )
        cls.other_group = Group.objects.create(
            description='Другой тестовый заголовок',
            title='Другой тестовый титл',
            slug='test-other-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def check_the_object_context_matches(self, post):
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.id, self.post.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/profile.html': (
                reverse(
                    'posts:profile', kwargs={'username': self.user.username}
                )
            )
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context.get('page_obj')[0]
        self.check_the_object_context_matches(post)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.post.author})
        )
        post = response.context.get('page_obj')[0]
        self.assertEqual(response.context.get('author'), self.post.author)
        self.check_the_object_context_matches(post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context.get('page_obj')[0]
        self.check_the_object_context_matches(post)
        self.assertEqual(response.context.get('group'), self.group)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})))
        post = response.context.get('post')
        self.check_the_object_context_matches(post)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        response = self.authorized_client.get(
            reverse(
                "posts:group_list", kwargs={"slug": self.other_group.slug}
            )
        )
        self.assertEqual(len(response.context.get('page_obj')), 0)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            description='Тестовый заголовок',
            title='Тестовый титл',
            slug='test-slug',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')

    def test_paginator(self):
        """Пагинатор корректно разбивает и выводит записи постранично"""
        posts = [Post(text=f'Тестовый текст {i}',
                      group=self.group,
                      author=self.user) for i in range(13)]
        Post.objects.bulk_create(posts)
        paginator_address = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for paginator in paginator_address:
            with self.subTest(paginator=paginator):
                response = self.client.get(paginator)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.client.get(paginator + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
