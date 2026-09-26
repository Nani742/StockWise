from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledLoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("features/", views.features, name="features"),
    path("help/", views.help_page, name="help"),
    path("contact/", views.contact, name="contact"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="core/login.html",
            authentication_form=StyledLoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-panel/message/<int:pk>/resolve/", views.resolve_message, name="resolve_message"),
    path("admin-panel/post/<int:pk>/delete/", views.delete_post, name="delete_post"),
]
