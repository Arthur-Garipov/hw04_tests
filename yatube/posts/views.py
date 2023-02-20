from django.shortcuts import render, get_object_or_404, redirect
from .paginate import pagination
from .models import Post, Group, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm

PER_PAGE = 10


def index(request):
    posts = Post.objects.all().order_by('-pub_date')
    template = 'posts/index.html'
    return render(request, template, {
        'page_obj': pagination(request, posts, PER_PAGE)}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': pagination(request, post_list, PER_PAGE)}
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    context = {
        'page_obj': pagination(request, post_list, PER_PAGE),
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_selected = Post.objects.get(pk=post_id)
    context = {
        'post': post_selected,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    groups = Group.objects.all()
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    else:
        form = PostForm()
        return render(request, 'posts/create_post.html', {
            'form': form, 'groups': groups
        })


@login_required
def post_edit(request, post_id):
    groups = Group.objects.all()
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form, 'is_edit': True, 'groups': groups
    })
