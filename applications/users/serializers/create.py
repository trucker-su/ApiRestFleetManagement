import random
import string

from django.contrib.auth import get_user_model
from rest_framework import serializers

from applications.users.models import User
from utils.email.users import send_created_user_email

pass_length = 8


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ['email', 'fullname']

    def save(self):
        user = User(email=self.validated_data['email'],
                    fullname=self.validated_data['fullname'])

        password = ''.join(random.choice(string.ascii_letters) for i in range(pass_length))

        user.set_password(password)
        user.save()
        send_created_user_email(user, password)
        return user
