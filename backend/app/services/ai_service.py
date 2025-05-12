from typing import Dict, Any, List, Optional
from app.models.schemas import IssueType, Language, ImageAnalysis
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
from PIL import Image
import os
from app.core.config import settings

class AIService:
    def __init__(self):
        self.issue_classifier = None
        self.image_analyzer = None
        self.text_generator = None
        self._initialize_models()

    def _initialize_models(self):
        # Initialize issue classification model
        model_name = "distilbert-base-uncased"  # Replace with your fine-tuned model
        self.issue_classifier = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name
        )

        # Initialize image analysis model
        self.image_analyzer = pipeline(
            "image-classification",
            model="microsoft/resnet-50"  # Replace with your fine-tuned model
        )

        # Initialize text generation model
        self.text_generator = pipeline(
            "text-generation",
            model="gpt2"  # Replace with your fine-tuned model
        )

    async def classify_issue(self, text: str) -> Dict[str, Any]:
        """Classify the issue type from customer description."""
        result = self.issue_classifier(text)
        return {
            "issue_type": result[0]["label"],
            "confidence": result[0]["score"]
        }

    async def analyze_image(self, image_path: str) -> ImageAnalysis:
        """Analyze uploaded image for issues."""
        try:
            image = Image.open(image_path)
            results = self.image_analyzer(image)
            print('Image analysis results:', results)
            # Process results and determine if issues are detected
            issues_detected = []
            confidence_scores = []
            for result in results:
                if result["score"] > settings.CONFIDENCE_THRESHOLD:
                    issues_detected.append(result["label"])
                    confidence_scores.append(result["score"])
            return ImageAnalysis(
                issue_detected=len(issues_detected) > 0,
                confidence_score=max(confidence_scores) if confidence_scores else 0.0,
                detected_issues=issues_detected,
                image_quality="good" if len(issues_detected) == 0 else "issues_detected",
                analysis_summary=self._generate_image_summary(issues_detected)
            )
        except Exception as e:
            return ImageAnalysis(
                issue_detected=False,
                confidence_score=0.0,
                detected_issues=[],
                image_quality="error",
                analysis_summary=f"Error analyzing image: {str(e)}"
            )

    def _generate_image_summary(self, issues: List[str]) -> str:
        """Generate a human-readable summary of image analysis."""
        if not issues:
            return "No issues detected in the image."
        return f"Detected issues: {', '.join(issues)}"

    async def generate_response(
        self,
        issue_type: IssueType,
        description: str,
        language: Language,
        image_analysis: Optional[ImageAnalysis] = None
    ) -> Dict[str, Any]:
        """Generate appropriate response based on issue type and analysis."""
        # Combine all information for context
        context = f"Issue Type: {issue_type}\nDescription: {description}"
        if image_analysis:
            context += f"\nImage Analysis: {image_analysis.analysis_summary}"

        # Generate response based on context
        response = self.text_generator(
            context,
            max_length=100,
            num_return_sequences=1
        )[0]["generated_text"]

        # Determine if human intervention is needed
        requires_human = (
            image_analysis.issue_detected if image_analysis else False
        ) or (
            issue_type in [IssueType.ESCALATION, IssueType.REFUND_QUERY]
        )

        return {
            "response": response,
            "requires_human": requires_human,
            "confidence_score": 0.8,  # This should be calculated based on model confidence
            "suggested_actions": self._get_suggested_actions(issue_type)
        }

    def _get_suggested_actions(self, issue_type: IssueType) -> List[str]:
        """Get suggested actions based on issue type."""
        action_map = {
            IssueType.PACKAGING_SPILLAGE: ["Request refund", "Request replacement"],
            IssueType.MISSING_ITEM: ["Request missing items", "Request partial refund"],
            IssueType.FOOD_QUALITY: ["Request refund", "Report to vendor"],
            IssueType.ORDER_CANCELLATION: ["Cancel order", "Check cancellation policy"],
            IssueType.REFUND_QUERY: ["Check refund status", "Initiate refund process"],
            IssueType.WRONG_ADDRESS: ["Update delivery address", "Contact rider"],
            IssueType.VENDOR_ISSUE: ["Report to vendor", "Request refund"],
            IssueType.RIDER_ISSUE: ["Report rider", "Request new rider"],
            IssueType.DELIVERY_STATUS: ["Track order", "Contact rider"],
            IssueType.ESCALATION: ["Connect to human agent"]
        }
        return action_map.get(issue_type, ["Contact support"]) 