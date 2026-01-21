from django.urls import path

from partners import views

urlpatterns = [
    path("", views.index, name="partners-index"),
]
