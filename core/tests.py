from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Post, Comment, Like, Activity, FeedAlgorithm
from django.contrib.contenttypes.models import ContentType
import json

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)

    def test_register(self):
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'newpassword123'}
        response = self.client.post('/api/register/', data)
        print(f"Register response: {response.status_code}, {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_create_post(self):
        data = {'content': 'This is a test post'}
        response = self.client.post('/api/posts/', data)
        print(f"Create post response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.get().content, 'This is a test post')

    def test_create_comment(self):
        post = Post.objects.create(user=self.user, content='Original post')
        data = {'post': post.id, 'content': 'This is a test comment'}
        response = self.client.post('/api/comments/', data)
        print(f"Create comment response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get().content, 'This is a test comment')

    def test_create_like_for_post(self):
        post = Post.objects.create(user=self.user, content='Likeable post')
        content_type = ContentType.objects.get_for_model(Post)
        data = {'content_type': content_type.id, 'object_id': post.id}
        response = self.client.post('/api/likes/', data)
        print(f"Create like for post response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(Like.objects.filter(content_type=content_type, object_id=post.id).count(), 1)

    def test_create_like_for_comment(self):
        post = Post.objects.create(user=self.user, content='Original post')
        comment = Comment.objects.create(user=self.user, post=post, content='Likeable comment')
        content_type = ContentType.objects.get_for_model(Comment)
        data = {'content_type': content_type.id, 'object_id': comment.id}
        response = self.client.post('/api/likes/', data)
        print(f"Create like for comment response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)
        self.assertEqual(Like.objects.filter(content_type=content_type, object_id=comment.id).count(), 1)

    def test_get_feed_with_algorithm(self):
        # Create posts
        post1 = Post.objects.create(user=self.user, content='High priority post')
        post2 = Post.objects.create(user=self.user, content='Low priority post')

        # Create activities for these posts
        activity1 = Activity.objects.create(user=self.user, action='post', content_object=post1)
        activity2 = Activity.objects.create(user=self.user, action='post', content_object=post2)

        # Create a feed algorithm that prioritizes posts with 'High' in the content
        algorithm = FeedAlgorithm.objects.create(
            name='Priority Algorithm',
            description='Prioritizes posts with "High" in the content',
            query=json.dumps({"content__icontains": "High"}),
            weight=2.0,
            is_active=True
        )
        print(f"Algorithm ID: {algorithm.id}, query: {algorithm.query}, weight: {algorithm.weight}")

        response = self.client.get('/api/activities/feed/')
        print(f"Get feed with algorithm response: {response.status_code}")
        print(f"Response data: {json.dumps(response.data, indent=2)}")
        
        for i, activity_data in enumerate(response.data):
            activity = Activity.objects.get(id=activity_data['id'])
            post = Post.objects.get(id=activity.object_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Check if the high priority post is first in the feed
        high_priority_post = Post.objects.get(content='High priority post')
        self.assertEqual(response.data[0]['object_id'], high_priority_post.id)

    def test_multiple_feed_algorithms(self):
        # Create posts
        post1 = Post.objects.create(user=self.user, content='High priority post')
        post2 = Post.objects.create(user=self.user, content='Medium priority post')
        post3 = Post.objects.create(user=self.user, content='Low priority post')

        # Create activities for these posts
        for post in [post1, post2, post3]:
            activity = Activity.objects.create(user=self.user, action='post', content_object=post)
            print(f"Activity ID: {activity.id}, object_id: {activity.object_id}, created_at: {activity.created_at}")

        # Create multiple feed algorithms
        algo1 = FeedAlgorithm.objects.create(
            name='High Priority Algorithm',
            description='Prioritizes posts with "High" in the content',
            query=json.dumps({"content__icontains": "High"}),
            weight=3.0,
            is_active=True
        )
        algo2 = FeedAlgorithm.objects.create(
            name='Medium Priority Algorithm',
            description='Prioritizes posts with "Medium" in the content',
            query=json.dumps({"content__icontains": "Medium"}),
            weight=2.0,
            is_active=True
        )

        response = self.client.get('/api/activities/feed/')

        for i, activity_data in enumerate(response.data):
            activity = Activity.objects.get(id=activity_data['id'])
            post = Post.objects.get(id=activity.object_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Check if the posts are in the correct order
        self.assertEqual(response.data[0]['object_id'], post1.id)  # High priority
        self.assertEqual(response.data[1]['object_id'], post2.id)  # Medium priority
        self.assertEqual(response.data[2]['object_id'], post3.id)  # Low priority

    def test_update_post(self):
        post = Post.objects.create(user=self.user, content='Original content')
        data = {'content': 'Updated content'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)
        print(f"Update post response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.get(id=post.id).content, 'Updated content')

    def test_delete_post(self):
        post = Post.objects.create(user=self.user, content='Delete me')
        response = self.client.delete(f'/api/posts/{post.id}/')
        print(f"Delete post response: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_create_nested_comment(self):
        post = Post.objects.create(user=self.user, content='Original post')
        parent_comment = Comment.objects.create(user=self.user, post=post, content='Parent comment')
        data = {'post': post.id, 'content': 'Nested comment', 'parent': parent_comment.id}
        response = self.client.post('/api/comments/', data)
        print(f"Create nested comment response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(Comment.objects.filter(parent=parent_comment).count(), 1)

    def test_get_user_posts(self):
        Post.objects.create(user=self.user, content='User post 1')
        Post.objects.create(user=self.user, content='User post 2')
        response = self.client.get(f'/api/posts/?user={self.user.id}')
        print(f"Get user posts response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_feed_algorithm(self):
        data = {
            'name': 'Test Algorithm',
            'description': 'This is a test algorithm',
            'query': '{"user__username": "testuser"}',
            'weight': 1.5,
            'is_active': True
        }
        response = self.client.post('/api/feed-algorithms/', data)
        print(f"Create feed algorithm response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FeedAlgorithm.objects.count(), 1)
        self.assertEqual(FeedAlgorithm.objects.get().name, 'Test Algorithm')