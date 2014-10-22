#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework import serializers


class SessionSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField('get_account')
    messages = serializers.SerializerMethodField('get_messages')

    def get_account(self, obj):
        request = self.context.get('request')
        return reverse('account', kwargs={'username': request.user.username}, request=request)

    def get_messages(self, obj):
        request = self.context.get('request')
        return [{
            'text': msg.message,
            'tags': msg.tags
            } for msg in messages.get_messages(request)]

    class Meta:
        model = Session
        fields = ('account', 'messages')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            self._user = authenticate(username=username, password=password)
            if not self._user:
                raise serializers.ValidationError('Invalid username and/or login')

        return attrs

    def restore_object(self, attrs, instance=None):
        if self.is_valid(): return self._user
        return instance


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    def validate_username(self, attrs, source):
        username = attrs.get(source)
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('Account with this username already exists')
        return attrs

    def save(self, **kw):
        User.objects.create_user(
            self.object.username,
            email=self.object.email,
            password=self.object.password
            )
        return authenticate(username=self.object.username, password=self.object.password)

    class Meta:
        model = User
        fields = ('username', 'password', 'email')
