from django.urls import path
from . import views
from .views import image_gallery_view, select_image_item

urlpatterns = [
    path('generateImage', views.generate_image, name='generateImage'),
    path('imageGallery/', image_gallery_view, name='imageGallery'),
    path('selectImageItem', select_image_item, name='selectImageItem'),
]
