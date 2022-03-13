from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def authorized_only(func):
    def check_user(request, *args, **kwargs):
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        return redirect('/auth/login/')
    return check_user


POSTS_PER_PAGE = 10
TIME_OF_CASHING = 20


@cache_page(TIME_OF_CASHING)
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_post(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user = request.user
    following = False
    if user.is_authenticated and Follow.objects.filter(
            user=user, author=author):
        following = True
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, pk):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects, pk=pk)
    comments = Comment.objects.filter(post=post)
    form_comment = CommentForm(request.POST or None)
    post_obj = Post.objects.all()
    context = {
        'post': post,
        'comments': comments,
        'form': form_comment,
        'post_obj': post_obj,
    }
    return render(request, template, context)


@authorized_only
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, template, {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


def post_edit(request, pk):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', pk=pk)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': True,
            'post': post,
        }
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', pk=pk)


@authorized_only
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', pk=pk)


@authorized_only
def follow_index(request):
    template = 'posts/follow.html'
    authors = Follow.objects.filter(user=request.user).values_list(
        'author', flat=True)
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@authorized_only
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (request.user != author):
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:follow_index')


@authorized_only
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
