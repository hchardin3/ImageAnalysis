from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import json
from ultralytics import YOLO
from PIL import Image, ImageDraw

yolo_model = YOLO('yolov8n.pt')

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
            data = json.loads(request.body.decode('utf-8'))
            file_url = data.get('file_url')
            if not file_url:
                return JsonResponse({'success': False, 'error': 'No file URL provided.'})

            # Delete the uploaded file
            file_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(file_url))
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete test_result.json
            result_path = os.path.join(settings.MEDIA_ROOT, "test_result.json")
            if os.path.exists(result_path):
                os.remove(result_path)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def analyze_image(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            image_url = data.get('file_url')
            if not image_url:
                return JsonResponse({'success': False, 'error': 'No image URL provided.'})

            # Construct the full image path
            image_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(image_url))
            if not os.path.exists(image_path):
                return JsonResponse({'success': False, 'error': 'Image file not found.'})

            # Perform object detection using YOLO (your existing logic)
            results = yolo_model(image_path)
            detections = results[0].boxes.data.tolist()

            # Process detections
            analyzed_data = []
            for detection in detections:
                x1, y1, x2, y2, confidence, class_id = detection
                label = results[0].names[int(class_id)]
                analyzed_data.append({
                    'label': label,
                    'confidence': round(float(confidence), 2),
                    'box': [int(x1), int(y1), int(x2), int(y2)],
                })

            # Return response without saving an analyzed image
            return JsonResponse({
                'success': True,
                'image_url': image_url,
                'detections': analyzed_data
            })

        except Exception as e:
            print(f"Error during analysis: {e}")  # Debugging
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})