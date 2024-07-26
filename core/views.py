from rest_framework import viewsets, status
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer, PostSerializer, CommentSerializer, LikeSerializer, ActivitySerializer, FeedAlgorithmSerializer
from .models import Post, Comment, Like, Activity, FeedAlgorithm
from .services import FeedService

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

    def perform_create(self, serializer):
        content_type_id = self.request.data.get('content_type')
        content_type = ContentType.objects.get(id=content_type_id)
        serializer.save(user=self.request.user, content_type=content_type)

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    @action(detail=False, methods=['get'])
    def feed(self, request):
        page = int(request.query_params.get('page', 1))
        feed = FeedService.get_feed(request.user, page=page)
        serializer = self.get_serializer(feed, many=True)
        return Response(serializer.data)
        
class FeedAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = FeedAlgorithm.objects.all()
    serializer_class = FeedAlgorithmSerializer

@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)