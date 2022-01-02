from django.conf import settings
from ..models import News
import datetime

class AddNewsAttribute:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        url     = request.get_full_path()
        if request.method == "GET" and settings.MEDIA_URL not in url and settings.STATIC_URL not in url:
            today           = datetime.date.today()
            request.NEWS    = News.objects.filter( start_date__lte=today, end_date__gte=today).order_by("-dt")

        response = self.get_response(request)

        return response

