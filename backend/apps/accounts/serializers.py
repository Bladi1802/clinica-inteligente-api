from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "phone")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.PATIENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class PatientCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "phone")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.PATIENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class StaffUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role", "phone")

    def validate_role(self, value):
        if value not in {User.Role.DOCTOR, User.Role.CLINIC}:
            raise serializers.ValidationError(
                "Solo se permite crear usuarios con rol DOCTOR o CLINIC."
            )
        return value

    def validate(self, attrs):
        request = self.context["request"]
        requester_role = getattr(request.user, "role", None)
        target_role = attrs.get("role")

        if requester_role == User.Role.CLINIC and target_role != User.Role.DOCTOR:
            raise serializers.ValidationError(
                {"role": "CLINIC solo puede crear usuarios DOCTOR."}
            )

        if requester_role not in {User.Role.CLINIC, User.Role.DOCTOR} and not request.user.is_superuser:
            raise serializers.ValidationError(
                {"detail": "No tienes permiso para crear personal."}
            )

        if requester_role == User.Role.DOCTOR and not request.user.is_superuser:
            raise serializers.ValidationError(
                {"detail": "DOCTOR no puede crear personal."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
