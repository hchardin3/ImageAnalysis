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

def analyze_image(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            image_url = data.get('file_url')  # Get file_url from JSON
            print(f"Received file_url from frontend: {image_url}")  # Debugging

            if not image_url:
                print("No image URL provided.")  # Debugging
                return JsonResponse({'success': False, 'error': 'No image URL provided in request.'})

            # Construct the full image path
            image_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(image_url))
            print(f"Constructed image path: {image_path}")  # Debugging

            if not os.path.exists(image_path):
                print(f"Image file not found at path: {image_path}")  # Debugging
                return JsonResponse({'success': False, 'error': 'Image file not found.'})


            # Perform object detection using YOLO
            print("Running YOLO detection...")  # Debug log
            results = yolo_model(image_path)
            detections = results[0].boxes.data.tolist()  # Extract detections
            print(f"YOLO detections: {detections}")  # Debug log

            # Load image for drawing bounding boxes
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            analyzed_data = []

            for detection in detections:
                x1, y1, x2, y2, confidence, class_id = detection
                label = results[0].names[int(class_id)]  # Get class label
                print(f"Detection: {label}, Confidence: {confidence}, Box: {[x1, y1, x2, y2]}")  # Debug log
                analyzed_data.append({
                    'label': label,
                    'confidence': round(float(confidence), 2),
                    'box': [int(x1), int(y1), int(x2), int(y2)],
                })

                # Draw bounding box and label on the image
                draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
                draw.text((x1, y1), f"{label} ({round(confidence, 2)})", fill='red')

            # Save analyzed image
            analyzed_image_path = os.path.join(settings.MEDIA_ROOT, f"analyzed_{os.path.basename(image_path)}")
            img.save(analyzed_image_path)
            print(f"Analyzed image saved to: {analyzed_image_path}")  # Debug log

            return JsonResponse({
                'success': True,
                'analyzed_image_url': os.path.join(settings.MEDIA_URL, f"analyzed_{os.path.basename(image_path)}"),
                'detections': analyzed_data
            })

        except Exception as e:
            print(f"Error during analysis: {e}")  # Debug log
            return JsonResponse({'success': False, 'error': str(e)})

    print("Invalid request method.")  # Debug log
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
