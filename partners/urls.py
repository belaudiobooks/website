from django.urls import path

from partners import views

app_name = "partners"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("<int:partner_id>/", views.dashboard, name="dashboard"),
    path("<int:partner_id>/agreements/", views.agreements, name="agreements"),
]
