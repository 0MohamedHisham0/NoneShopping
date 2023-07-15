
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('ai_image_generator.urls')),
    path('admin/', admin.site.urls),
]
