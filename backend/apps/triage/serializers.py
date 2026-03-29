from rest_framework import serializers

from .models import TriageAssessment


class TriageAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageAssessment
        fields = [
            "id",
            "appointment",
            "chief_complaint",
            "risk_level",
            "risk_score",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "appointment", "risk_level", "risk_score", "created_at", "updated_at"]
