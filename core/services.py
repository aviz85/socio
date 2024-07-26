import json
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast, Coalesce
from django.db.models import Case, When, Value, Subquery, OuterRef
from .models import Activity, FeedAlgorithm, Post
from django.contrib.contenttypes.models import ContentType

class FeedService:
    @staticmethod
    def get_feed(user, page=1, items_per_page=20):
        algorithms = FeedAlgorithm.objects.filter(is_active=True)
        if not algorithms.exists():
            return Activity.objects.order_by('-created_at')[:items_per_page]
        
        post_content_type = ContentType.objects.get_for_model(Post)
        
        ranking_cases = []
        
        for algorithm in algorithms:
            query_dict = json.loads(algorithm.query)
            algorithm_query = Q()
            for key, value in query_dict.items():
                if key == 'content__icontains':
                    algorithm_query &= Q(
                        content_type=post_content_type,
                        object_id__in=Post.objects.filter(content__icontains=value).values('id')
                    )
                else:
                    algorithm_query &= Q(**{key: value})
            
            ranking_cases.append(
                When(algorithm_query, then=Value(algorithm.weight))
            )

        activities = Activity.objects.annotate(
            rank=Coalesce(Case(*ranking_cases, output_field=FloatField()), Value(0.0))
        ).order_by('-rank', '-created_at')

        print(f"SQL Query: {activities.query}")
        
        # Print out all activities with their ranks for debugging
        for activity in activities:
            content_object = activity.content_object
            print(f"Activity ID: {activity.id}, Object ID: {activity.object_id}, "
                  f"Content: {content_object.content if hasattr(content_object, 'content') else 'N/A'}, "
                  f"Rank: {activity.rank}, Created at: {activity.created_at}")

        return activities[(page-1)*items_per_page:page*items_per_page]