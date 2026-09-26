from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from analysis.models import WatchlistItem

from .forms import CommunityPostForm, ContactForm, RegisterForm
from .models import CommunityPost, ContactMessage


def home(request):
    return render(request, "core/home.html")


def features(request):
    return render(request, "core/features.html")


def help_page(request):
    return render(request, "core/help.html")


def contact(request):
    contact_form = ContactForm()
    post_form = CommunityPostForm()

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "post":
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to post in the community.")
                return redirect("login")
            post_form = CommunityPostForm(request.POST)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.author = request.user
                post.save()
                messages.success(request, "Your post is live in the community!")
                return redirect("contact")
        else:
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, "Thanks! Your message was sent. We'll reply by email.")
                return redirect("contact")

    posts = CommunityPost.objects.select_related("author")[:20]
    return render(request, "core/contact.html", {
        "contact_form": contact_form,
        "post_form": post_form,
        "posts": posts,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to StockWise, {user.first_name or user.username}!")
        return redirect("dashboard")
    return render(request, "core/register.html", {"form": form})


def is_staff(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(is_staff, login_url="home")
def admin_panel(request):
    context = {
        "user_count": User.objects.count(),
        "watch_count": WatchlistItem.objects.count(),
        "message_count": ContactMessage.objects.count(),
        "open_count": ContactMessage.objects.filter(is_resolved=False).count(),
        "post_count": CommunityPost.objects.count(),
        "recent_users": User.objects.order_by("-date_joined")[:8],
        "messages_list": ContactMessage.objects.all()[:10],
        "top_symbols": WatchlistItem.objects.values("symbol").annotate(n=Count("id")).order_by("-n")[:10],
        "recent_posts": CommunityPost.objects.select_related("author")[:5],
    }
    return render(request, "core/admin_panel.html", context)


@login_required
@user_passes_test(is_staff, login_url="home")
@require_POST
def resolve_message(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_resolved = not msg.is_resolved
    msg.save(update_fields=["is_resolved"])
    return redirect("admin_panel")


@login_required
@user_passes_test(is_staff, login_url="home")
@require_POST
def delete_post(request, pk):
    get_object_or_404(CommunityPost, pk=pk).delete()
    messages.info(request, "Post deleted.")
    return redirect("admin_panel")
