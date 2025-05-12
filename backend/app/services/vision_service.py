from google.cloud import vision
from typing import Dict, Any, List
import logging
import os
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS from settings: {credentials_path}")
        
        if not os.path.exists(credentials_path):
            raise ValueError(f"Google Cloud credentials file not found at: {credentials_path}")
        
        # Read and log the project ID from the credentials file
        try:
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
                logger.info(f"Credentials file project_id: {creds_data.get('project_id')}")
        except Exception as e:
            logger.error(f"Error reading credentials file: {str(e)}")
        
        logger.info(f"Initializing Vision API client with credentials from: {credentials_path}")
        self.client = vision.ImageAnnotatorClient.from_service_account_file(credentials_path)

        # Define food quality related categories
        self.food_quality_categories = {
            'freshness': ['fresh', 'stale', 'rotten', 'spoiled', 'moldy', 'expired'],
            'temperature': ['hot', 'cold', 'warm', 'frozen', 'thawed'],
            'presentation': ['messy', 'neat', 'organized', 'disorganized', 'spilled'],
            'packaging': ['damaged', 'intact', 'leaking', 'sealed', 'open'],
            'food_type': ['meat', 'vegetable', 'fruit', 'dairy', 'grain', 'dessert'],
            'cooking': ['undercooked', 'overcooked', 'raw', 'burnt', 'perfectly cooked']
        }

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze an image using Google Cloud Vision API with focus on food quality
        Returns a structured analysis of the image
        """
        try:
            # Create an image object from the URL
            image = vision.Image()
            image.source.image_uri = image_url

            # Perform multiple types of analysis
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
                vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION)
            ]

            # Perform the analysis
            response = self.client.annotate_image({
                'image': image,
                'features': features
            })

            # Process the results
            analysis = {
                'labels': [],
                'objects': [],
                'colors': [],
                'safe_search': {},
                'food_quality_analysis': {
                    'freshness': [],
                    'temperature': [],
                    'presentation': [],
                    'packaging': [],
                    'food_type': [],
                    'cooking': []
                },
                'issues_detected': False,
                'analysis_summary': ''
            }

            # Process labels and categorize them
            for label in response.label_annotations:
                label_info = {
                    'description': label.description,
                    'confidence': label.score
                }
                analysis['labels'].append(label_info)
                
                # Categorize the label into food quality categories
                label_desc = label.description.lower()
                for category, keywords in self.food_quality_categories.items():
                    if any(keyword in label_desc for keyword in keywords):
                        analysis['food_quality_analysis'][category].append(label_info)

            # Process objects
            for object_ in response.localized_object_annotations:
                analysis['objects'].append({
                    'name': object_.name,
                    'confidence': object_.score
                })

            # Process dominant colors
            for color in response.image_properties_annotation.dominant_colors.colors:
                analysis['colors'].append({
                    'red': color.color.red,
                    'green': color.color.green,
                    'blue': color.color.blue,
                    'score': color.score
                })

            # Process safe search
            safe_search = response.safe_search_annotation
            analysis['safe_search'] = {
                'adult': safe_search.adult.name,
                'violence': safe_search.violence.name,
                'spoof': safe_search.spoof.name,
                'medical': safe_search.medical.name,
                'racy': safe_search.racy.name
            }

            # Check for food quality issues
            quality_issues = []
            for category, labels in analysis['food_quality_analysis'].items():
                if category in ['freshness', 'temperature', 'presentation', 'packaging', 'cooking']:
                    for label in labels:
                        if label['confidence'] > 0.7:  # Only consider high confidence detections
                            quality_issues.append(f"{label['description']} ({category})")

            analysis['issues_detected'] = len(quality_issues) > 0

            # Generate a detailed summary
            summary_parts = []
            
            # Add food type information
            food_types = analysis['food_quality_analysis']['food_type']
            if food_types:
                summary_parts.append("Food items detected:")
                for food in food_types:
                    summary_parts.append(f"- {food['description']} (confidence: {food['confidence']:.2f})")

            # Add quality issues
            if quality_issues:
                summary_parts.append("\nQuality issues detected:")
                for issue in quality_issues:
                    summary_parts.append(f"- {issue}")
            else:
                summary_parts.append("\nNo significant quality issues detected.")

            # Add packaging status
            packaging_issues = analysis['food_quality_analysis']['packaging']
            if packaging_issues:
                summary_parts.append("\nPackaging status:")
                for issue in packaging_issues:
                    summary_parts.append(f"- {issue['description']} (confidence: {issue['confidence']:.2f})")

            analysis['analysis_summary'] = "\n".join(summary_parts)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing image with Google Vision API: {str(e)}")
            raise 