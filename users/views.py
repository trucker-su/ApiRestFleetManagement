from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from shared.permissions import IsAdmin
from users.models import Role
from users.serializers.create import RegistrationSerializer
from users.serializers.simple import SimpleUserSerializer
from users.serializers.special import UpdateUserSerializer


class UserViewSet(viewsets.ViewSet):
    """
    This entire endpoint class and its methods (endpoints) are only available if requester is admin.
    """

    def list(self, request):
        """
        It returns all users.
        :param request:
        :return: users
        """
        queryset = get_user_model().objects.all()
        serializer = SimpleUserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        It returns the user given an id.
        :param request:
        :param pk: user id
        :return:
        """
        queryset = get_user_model().objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = SimpleUserSerializer(user)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        It deletes an user and all his relations (reservations, incidents, tickets).
        If requester tries to delete himself, server respond with 403 ERROR.
        :param request:
        :param pk: user id
        :return:
        """
        requester = self.request.user
        queryset = get_user_model().objects.all()
        user = get_object_or_404(queryset, pk=pk)
        if requester == user:
            return Response(status=HTTP_403_FORBIDDEN)
        user.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def update(self, request, pk=None):
        """
        It update the data of a user.
        """
        requester = self.request.user
        queryset = get_user_model().objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UpdateUserSerializer(user, self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # Create method is located in /register endpoint
    def get_permissions(self):
        return [permission() for permission in [permissions.IsAuthenticated, IsAdmin]]


class RegistrationViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = RegistrationSerializer(data=self.request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        # Only admin can register users.
        return [permission() for permission in [permissions.IsAuthenticated, IsAdmin]]


class AdminAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.role == Role.USER:
            return Response(status=HTTP_401_UNAUTHORIZED)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key
        })