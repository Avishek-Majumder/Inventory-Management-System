import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'bio', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_phone_number(self, value):
        if value and not re.fullmatch(r'\+?[0-9\-\s]{7,20}', value):
            raise serializers.ValidationError('Enter a valid phone number.')
        return value


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        instance.save()
        if profile_data is not None:
            profile, _ = Profile.objects.get_or_create(user=instance)
            for attribute, value in profile_data.items():
                setattr(profile, attribute, value)
            profile.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)
