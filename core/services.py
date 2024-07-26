import json
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast, Coalesce
from django.db.models import Case, When, Value, Subquery, OuterRef
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.utils import timezone
from .models import Activity, FeedAlgorithm, Post

class FeedService:
    @staticmethod
    def get_feed(user, page=1, items_per_page=20):
        algorithms = FeedAlgorithm.objects.filter(is_active=True)
        post_content_type = ContentType.objects.get_for_model(Post)
        
        base_query = Activity.objects.filter(content_type=post_content_type)
        
        if not algorithms.exists():
            activities = base_query.order_by('-created_at')
        else:
            ranking_cases = []
            
            for algorithm in algorithms:
                try:
                    query_dict = json.loads(algorithm.query)
                    algorithm_query = Q()
                    for key, value in query_dict.items():
                        if key.startswith('content__'):
                            post_ids = Post.objects.filter(**{key: value}).values('id')
                            algorithm_query &= Q(object_id__in=post_ids)
                    
                    if algorithm_query:
                        ranking_cases.append(
                            When(algorithm_query, then=Value(algorithm.weight))
                        )
                except json.JSONDecodeError:
                    print(f"Invalid JSON in algorithm {algorithm.name}: {algorithm.query}")
                except FieldError:
                    print(f"Invalid field in algorithm {algorithm.name}: {algorithm.query}")
            
            if ranking_cases:
                now = timezone.now()
                activities = base_query.annotate(
                    algorithm_rank=Case(*ranking_cases, default=Value(0.0), output_field=FloatField()),
                    time_diff=ExpressionWrapper(now - F('created_at'), output_field=FloatField()),
                    recency_score=ExpressionWrapper(1 / (1 + F('time_diff') / 86400), output_field=FloatField()),
                    combined_rank=ExpressionWrapper(
                        F('algorithm_rank') + F('recency_score'),
                        output_field=FloatField()
                    )
                ).order_by('-combined_rank', '-created_at')
            else:
                activities = base_query.order_by('-created_at')
        
        start = (page - 1) * items_per_page
        end = start + items_per_page
        
        activity_list = list(activities[start:end])
        post_ids = [activity.object_id for activity in activity_list]
        posts = Post.objects.filter(id__in=post_ids)
        post_dict = {post.id: post for post in posts}
        
        feed_items = []
        for activity in activity_list:
            post = post_dict.get(activity.object_id)
            if post:
                feed_items.append({
                    'id': activity.id,
                    'object_id': activity.object_id,
                    'content': post.content,
                    'created_at': activity.created_at,
                    'algorithm_rank': getattr(activity, 'algorithm_rank', 0.0),
                    'recency_score': getattr(activity, 'recency_score', 0.0),
                    'combined_rank': getattr(activity, 'combined_rank', 0.0)
                })
        
        return feed_items