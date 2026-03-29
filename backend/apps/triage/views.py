from django.shortcuts import render

# Create your views here.

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from scheduling.models import Appointment

from .models import TriageAssessment
from .serializers import TriageAssessmentSerializer


def _calculate_risk(chief_complaint: str, answers: dict):
    score = 0
    text = (chief_complaint or "").lower()

    # Palabras de alarma (simple MVP rule-based)
    red_flags = ["dolor toracico", "falta de aire", "sangrado", "desmayo", "convulsion", "fiebre alta"]
    if any(flag in text for flag in red_flags):
        score += 40

    for _, value in (answers or {}).items():
        if isinstance(value, bool):
            score += 15 if value else 0
        elif isinstance(value, int):
            score += max(0, min(value, 10)) * 3
        elif isinstance(value, str):
            v = value.strip().lower()
            if v in {"si", "yes", "true", "alto", "severo"}:
                score += 10

    score = min(score, 100)

    if score >= 70:
        level = TriageAssessment.RiskLevel.HIGH
    elif score >= 35:
        level = TriageAssessment.RiskLevel.MEDIUM
    else:
        level = TriageAssessment.RiskLevel.LOW

    return score, level


@api_view(["GET", "POST", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def appointment_triage(request, pk: int):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        pk=pk,
    )

    user = request.user
    is_patient_owner = appointment.patient_id == user.id
    is_assigned_doctor = appointment.doctor_id == user.id
    is_clinic = getattr(user, "role", None) == "CLINIC"

    triage = TriageAssessment.objects.filter(appointment=appointment).first()

    # GET -> patient dueño, doctor asignado o clinic
    if request.method == "GET":
        if not (is_patient_owner or is_assigned_doctor or is_clinic):
            return Response({"detail": "No tienes permiso para ver el triage de esta cita."}, status=status.HTTP_403_FORBIDDEN)

        if not triage:
            return Response({"detail": "No existe triage para esta cita."}, status=status.HTTP_404_NOT_FOUND)

        return Response(TriageAssessmentSerializer(triage).data, status=status.HTTP_200_OK)

    # POST -> patient dueño / doctor asignado / clinic
    if request.method == "POST":
        if not (is_patient_owner or is_assigned_doctor or is_clinic):
            return Response({"detail": "No tienes permiso para crear triage en esta cita."}, status=status.HTTP_403_FORBIDDEN)

        if triage:
            return Response({"detail": "Ya existe un triage para esta cita."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TriageAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chief_complaint = serializer.validated_data.get("chief_complaint", "")
        answers = serializer.validated_data.get("answers", {})
        risk_score, risk_level = _calculate_risk(chief_complaint, answers)

        created = serializer.save(
            appointment=appointment,
            risk_score=risk_score,
            risk_level=risk_level,
        )
        return Response(TriageAssessmentSerializer(created).data, status=status.HTTP_201_CREATED)

    # PATCH -> doctor asignado o clinic
    if request.method == "PATCH":
        if not (is_assigned_doctor or is_clinic):
            return Response({"detail": "Solo DOCTOR asignado o CLINIC puede actualizar triage."}, status=status.HTTP_403_FORBIDDEN)

        if not triage:
            return Response({"detail": "No existe triage para esta cita."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TriageAssessmentSerializer(triage, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        chief_complaint = serializer.validated_data.get("chief_complaint", triage.chief_complaint)
        answers = serializer.validated_data.get("answers", triage.answers)
        risk_score, risk_level = _calculate_risk(chief_complaint, answers)

        updated = serializer.save(risk_score=risk_score, risk_level=risk_level)
        return Response(TriageAssessmentSerializer(updated).data, status=status.HTTP_200_OK)

    # DELETE -> clinic
    if not is_clinic:
        return Response({"detail": "Solo CLINIC puede eliminar triage."}, status=status.HTTP_403_FORBIDDEN)

    if not triage:
        return Response({"detail": "No existe triage para esta cita."}, status=status.HTTP_404_NOT_FOUND)

    triage.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
