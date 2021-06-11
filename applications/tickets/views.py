from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT, HTTP_200_OK

from applications.reservations.utils import is_reservation_already_started
from applications.tickets.models import Ticket
from applications.tickets.serializers.create import CreateTicketSerializer
from applications.tickets.serializers.simple import SimpleTicketSerializer
from applications.tickets.services.solver import solve_ticket
from applications.users.models import Role
from applications.users.services import get_admin
from shared.permissions import IsOwnerReservationOrAdmin, IsNotDisabled
from utils.email.tickets import send_created_ticket_email


class TicketViewSet(viewsets.ViewSet):

    def list(self, request):
        """
        If take_all is True and requester is admin, it will return all tickets.
        Otherwise, it will return only the requester tickets.
        :param request:
        :return:
        """
        take_all = bool(self.request.query_params.get('take_all'))
        requester = self.request.user
        if requester.role == Role.ADMIN and take_all is True:
            queryset = Ticket.objects.all()
        else:
            queryset = requester.tickets.all()
        serializer = SimpleTicketSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        user = self.request.user
        serializer = CreateTicketSerializer(data=self.request.data)

        # Verify if the data request is valid
        if serializer.is_valid():
            reservation = serializer.validated_data['reservation']
            if is_reservation_already_started(reservation):
                return Response(status=HTTP_400_BAD_REQUEST)

            ticket = serializer.save(owner=user)
            admin = get_admin()
            send_created_ticket_email(admin, ticket)
            return Response(serializer.data)
        # If serializer is not valid send errors.
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        requester = self.request.user
        if requester.role == Role.ADMIN:
            queryset = Ticket.objects.all()
        else:
            queryset = requester.tickets.all()
        ticket = get_object_or_404(queryset, pk=pk)
        serializer = SimpleTicketSerializer(ticket)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        requester = self.request.user
        if requester.role == Role.ADMIN:
            queryset = Ticket.objects.all()
        else:
            queryset = requester.tickets.all()
        ticket = get_object_or_404(queryset, pk=pk)
        ticket.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def update(self, request, pk=None):
        ticket = Ticket.objects.get(pk=pk)
        data = self.request.data
        new_status = data['new_status']
        error = solve_ticket(ticket, new_status)
        errors = {'errors': error}
        if error:
            return Response(errors, status=HTTP_400_BAD_REQUEST)
        return Response(status=HTTP_200_OK)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsNotDisabled, IsOwnerReservationOrAdmin]
        else:
            # You must be authenticated and have access to the vehicle.
            permission_classes = [permissions.IsAuthenticated, IsNotDisabled]
        return [permission() for permission in permission_classes]
