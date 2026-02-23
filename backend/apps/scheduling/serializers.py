from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Service, AppointmentService


class AppointmentServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    duration_minutes = serializers.IntegerField(source="service.duration_minutes", read_only=True)

    class Meta:
        model = AppointmentService
        fields = [
            "id",
            "service",
            "service_name",
            "duration_minutes",
            "quantity",
            "price_at_booking",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    services = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            "id",
            "scheduled_at",
            "reason",
            "status",
            "services",
            "total_duration_minutes",
            "total_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "services",
            "total_duration_minutes",
            "total_price",
            "created_at",
            "updated_at",
        )

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("No se puede agendar una cita en el pasado.")
        return value

    def get_services(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj).select_related("service")
        return AppointmentServiceSerializer(qs, many=True).data

    def get_total_duration_minutes(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj).select_related("service")
        return sum((item.service.duration_minutes or 0) * (item.quantity or 1) for item in qs)

    def get_total_price(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj)
        total = 0
        for item in qs:
            price = item.price_at_booking or 0
            qty = item.quantity or 1
            total += price * qty
        return total


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "duration_minutes",
            "base_price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
