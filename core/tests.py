from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from .models import Post, Activity, FeedAlgorithm
from django.contrib.contenttypes.models import ContentType
import json
from freezegun import freeze_time
from .services import FeedService

class TestFeedAlgorithm(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.post_content_type = ContentType.objects.get_for_model(Post)

    def create_post(self, content, user=None, days_ago=0):
        user = user or self.user
        with freeze_time(timezone.now() - timezone.timedelta(days=days_ago)):
            post = Post.objects.create(user=user, content=content)
            Activity.objects.create(user=user, action='post', content_type=self.post_content_type, object_id=post.id)
        return post

    def create_algorithm(self, name, query, weight, is_active=True):
        return FeedAlgorithm.objects.create(
            name=name,
            description=f'Test algorithm: {name}',
            query=json.dumps(query),
            weight=weight,
            is_active=is_active
        )

    def get_feed(self, page=1):
        response = self.client.get(f'/api/activities/feed/?page={page}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_feed_without_algorithm(self):
        self.create_post("Newest post", days_ago=0)
        self.create_post("Middle post", days_ago=1)
        self.create_post("Oldest post", days_ago=2)

        feed = self.get_feed()
        self.assertEqual(len(feed), 3)
        self.assertEqual(feed[0]['content'], "Newest post")
        self.assertEqual(feed[2]['content'], "Oldest post")

    def test_single_algorithm(self):
        self.create_post("High priority post", days_ago=2)
        self.create_post("Normal post 1", days_ago=1)
        self.create_post("Normal post 2", days_ago=0)

        self.create_algorithm("Priority Algorithm", {"content__icontains": "High"}, weight=2.0)

        feed = self.get_feed()
        self.assertEqual(len(feed), 3)
        self.assertEqual(feed[0]['content'], "High priority post")

    def test_multiple_algorithms(self):
        self.create_post("High priority post", days_ago=2)
        self.create_post("Medium priority post", days_ago=1)
        self.create_post("Low priority post", days_ago=0)

        self.create_algorithm("High Priority", {"content__icontains": "High"}, weight=3.0)
        self.create_algorithm("Medium Priority", {"content__icontains": "Medium"}, weight=2.0)

        feed = self.get_feed()
        self.assertEqual(len(feed), 3)
        self.assertEqual(feed[0]['content'], "High priority post")
        self.assertEqual(feed[1]['content'], "Medium priority post")
        self.assertEqual(feed[2]['content'], "Low priority post")

    def test_algorithm_weight(self):
        self.create_post("Weighted post", days_ago=1)
        self.create_post("Recent post", days_ago=0)

        self.create_algorithm("Weighted Algorithm", {"content__icontains": "Weighted"}, weight=10.0)

        feed = self.get_feed()
        self.assertEqual(len(feed), 2)
        self.assertEqual(feed[0]['content'], "Weighted post")

    def test_inactive_algorithm(self):
        self.create_post("Inactive algorithm post", days_ago=1)
        self.create_post("Recent post", days_ago=0)

        self.create_algorithm("Inactive Algorithm", {"content__icontains": "Inactive"}, weight=10.0, is_active=False)

        feed = self.get_feed()
        self.assertEqual(len(feed), 2)
        self.assertEqual(feed[0]['content'], "Recent post")

    def test_complex_algorithm(self):
        test_cases = [
            ("High priority urgent", "High priority urgent"),
            ("Urgent high priority", "Urgent high priority"),
            ("Just urgent", "Just urgent"),
            ("Only high priority", "Only high priority"),
            ("Normal post", "Normal post"),
        ]
        
        for content, expected_first in test_cases:
            with self.subTest(content=content):
                Activity.objects.all().delete()
                Post.objects.all().delete()
                FeedAlgorithm.objects.all().delete()
                
                self.create_post(content, days_ago=1)
                self.create_post("Normal post", days_ago=0)

                self.create_algorithm("Complex Algorithm", 
                                      {"content__icontains": "High", "content__icontains": "priority"}, 
                                      weight=3.0)
                self.create_algorithm("Urgent Algorithm", {"content__icontains": "urgent"}, weight=2.0)

                feed = self.get_feed()
                self.assertEqual(len(feed), 2)
                self.assertEqual(feed[0]['content'], expected_first)

    def test_algorithm_update(self):
        # Create posts
        self.create_post("Algorithm post", days_ago=2)
        self.create_post("Recent post", days_ago=0)

        # Create algorithm with low weight
        algorithm = self.create_algorithm("Test Algorithm", {"content__icontains": "Algorithm"}, weight=1.0)

        # Get initial feed
        initial_feed = self.get_feed()
        self.assertEqual(initial_feed[0]['content'], "Recent post", "Recent post should be first initially")
        self.assertEqual(initial_feed[1]['content'], "Algorithm post", "Algorithm post should be second initially")

        # Update algorithm weight
        algorithm.weight = 10.0
        algorithm.save()

        # Clear caches if any
        from django.core.cache import cache
        cache.clear()

        # Get updated feed
        updated_feed = self.get_feed()
        self.assertEqual(updated_feed[0]['content'], "Algorithm post", "Algorithm post should be first after update")
        self.assertEqual(updated_feed[1]['content'], "Recent post", "Recent post should be second after update")

        # Print debug information
        print("Initial feed:", [item['content'] for item in initial_feed])
        print("Updated feed:", [item['content'] for item in updated_feed])
        print("Algorithm weight:", algorithm.weight)
    
    def test_large_number_of_posts(self):
        # Create 100 posts
        for i in range(100):
            self.create_post(f"Post {i}", days_ago=100-i)

        self.create_algorithm("Even Numbers", {"content__regex": r"Post [0-9]*[02468]$"}, weight=2.0)

        feed = self.get_feed()
        self.assertEqual(len(feed), 20)  # Assuming default items_per_page is 20
        # Check that all returned posts are even-numbered
        for item in feed:
            post_number = int(item['content'].split()[-1])
            self.assertTrue(post_number % 2 == 0, f"Post number {post_number} is not even")

    def test_edge_case_empty_query(self):
        self.create_post("Test post")
        self.create_algorithm("Empty Query", {"content__icontains": ""}, weight=1.0)

        feed = self.get_feed()
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]['content'], "Test post")

    def test_invalid_algorithm_query(self):
        self.create_post("Test post")
        self.create_algorithm("Invalid Query", {"invalid_field": "value"}, weight=1.0)

        # The feed should still work, ignoring the invalid algorithm
        feed = self.get_feed()
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]['content'], "Test post")