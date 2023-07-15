import json
from datetime import timezone, datetime

from django.http import JsonResponse
from django.http import HttpResponse, JsonResponse

from .service.logo_folder_uploader import LogoFolderUploader

from .models import GeneratedImage
from django.shortcuts import render
from .models import GeneratedImageItem


def generate_image(request):
    if request.method == 'POST':
        logoList = json.loads(request.body)
        # Create an instance of the LogoFolderUploader class
        uploader = LogoFolderUploader(logoList)

        # Call the upload_logos method to start the process
        uploader.upload_logos()

        return HttpResponse('Image generated successfully!')
    else:
        return HttpResponse('Invalid request method.')


def image_gallery_view(request):
    images = GeneratedImage.objects.filter(
        is_selected=False,
        drive_image_url__isnull=False,
        drive_image_url__gt=''
    )

    context = {'images': images}
    return render(request, 'image_gallery.html', context)


def validate_select_image_item_response(selected_image_id):
    if selected_image_id is None:
        return False, None, None
    try:
        generate_image_item = GeneratedImageItem.objects.get(id=selected_image_id)
        if generate_image_item is None:
            return False, None, None
        if generate_image_item.is_selected is True:
            return False, None, None

        generate_image_id = generate_image_item.generated_image_id
        generate_image = GeneratedImage.objects.get(id=generate_image_id)

        if generate_image.is_selected is True:
            return False, None, None

    except GeneratedImageItem.DoesNotExist:
        return False, None, None
    except Exception:
        return False, None, None

    return True, generate_image_item, generate_image


def select_image_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_image_id = data.get("id")

        is_valid, generate_image_item, generate_image = validate_select_image_item_response(selected_image_id)
        if is_valid:
            generate_image_item.is_selected = True

            generate_image.is_selected = True
            generate_image.selected_image_id = generate_image_item.id
            generate_image.selected_at = datetime.now(tz=timezone.utc)

            generate_image_item.save()
            generate_image.save()

            return JsonResponse({'status': 'success'}, status=200)
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    # Return a JSON response with an error message if the request method is not POST
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
