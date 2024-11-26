from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import json

def index(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Handle the uploaded image
        image = request.FILES['image']
        fs = FileSystemStorage()
        file_path = fs.save(image.name, image)
        file_url = fs.url(file_path)

        # Return a JSON response with the file URL
        return JsonResponse({'file_url': file_url})

    return render(request, 'analyzer/index.html')

def delete_image(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            body = json.loads(request.body)
            file_url = body.get('file_url')

            if not file_url:
                return JsonResponse({'success': False, 'error': 'File URL not provided.'})

            # Construct the file path
            file_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(file_url))

            # Check if the file exists and delete it
            if os.path.exists(file_path):
                os.remove(file_path)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'File not found.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request.'})