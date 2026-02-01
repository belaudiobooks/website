from django.urls import path

from partners import jobs, views

app_name = "partners"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("login/<uuid:login_uuid>/", views.login_by_uuid, name="login_by_uuid"),
    path("logout/", views.logout_view, name="logout"),
    path("<int:partner_id>/", views.dashboard, name="dashboard"),
    path("<int:partner_id>/agreements/", views.agreements, name="agreements"),
    path("<int:partner_id>/sales/", views.sales, name="sales"),
    path(
        "<int:partner_id>/agreements/<int:agreement_id>/file/",
        views.download_agreement_file,
        name="download_agreement_file",
    ),
    path("job/sync_sales_reports", jobs.sync_sales_reports, name="sync_sales_reports"),
]
