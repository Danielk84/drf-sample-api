from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"token", views.BaseTokenAuthViewSet, basename="token")
router.register(r"articles", views.ArticleListViewSet, basename="articles")
router.register(r"user-article", views.UserArticleViewSet, basename="user-article")
router.register(r"admin-article", views.AdminArticleViewSet, basename="admin-article")

app_name = "api_app"

urlpatterns = router.urls