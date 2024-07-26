from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'likes', views.LikeViewSet)
router.register(r'activities', views.ActivityViewSet)
router.register(r'feed-algorithms', views.FeedAlgorithmViewSet)

urlpatterns = [
    path('', include(router.urls)),
]