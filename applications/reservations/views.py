import logging

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT

from applications.reservations.models import Reservation
from applications.reservations.serializers.create import CreateReservationSerializer
from applications.reservations.serializers.simple import SimpleReservationSerializer
from applications.users.models import Role
from shared.permissions import IsVehicleAllowedOrAdmin, IsNotDisabled

logger = logging.getLogger(__name__)


class ReservationViewSet(viewsets.ViewSet):

    def list(self, request):
        """
        If take_all is present as True, it will return all reservations.
        Otherwise, if take_all is False or is not present, it will return only requester reservations.
        :param request:
        :return: Returns a list of reservations.
        """
        take_all = bool(self.request.query_params.get('take_all'))
        logger.info('List reservations request received. [take_all: {}]'.format(take_all))
        requester = self.request.user
        if requester.role == Role.ADMIN and take_all is True:
            queryset = Reservation.objects.all()
        # If requester is not ADMIN and take_all is not True. Just get the requester reservations.
        else:
            queryset = requester.reservations.all()
        serializer = SimpleReservationSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Creates a reservation.
        :param request:
        :return:
        """
        logger.info('Create reservation request received.')
        requester = self.request.user
        serializer = CreateReservationSerializer(data=self.request.data)

        if not serializer.is_valid():
            log_error_serializing(serializer)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        serializer.save(owner=requester)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        logger.info('Retrieve reservation request received.')
        requester = self.request.user
        if requester.role == Role.ADMIN:
            queryset = Reservation.objects.all()
        else:
            queryset = requester.reservations.all()
        reservation = get_object_or_404(queryset, pk=pk)
        serializer = SimpleReservationSerializer(reservation)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        logger.info('Destroy reservation request received.')
        requester = self.request.user
        if requester == Role.ADMIN:
            queryset = Reservation.objects.all()
        else:
            queryset = requester.reservations.all()
        reservation = get_object_or_404(queryset, pk=pk)
        reservation.is_cancelled = True
        reservation.save()
        return Response(status=HTTP_204_NO_CONTENT)

    # THIS RESTRICT TO REQUESTER MAKE A RESERVATION OF VEHICLE TYPES THAT HE DOESN'T HAVE ACCESS.
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsNotDisabled, IsVehicleAllowedOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated, IsNotDisabled]
        return [permission() for permission in permission_classes]


def log_error_serializing(serializer):
    logger.error("Reservation couldn't be serialized with {} because of {}."
                 .format(serializer.__class__.__name__, serializer.errors))
