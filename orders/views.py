from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Order, PromoCode
from .serializers import OrderCreateSerializer, OrderSerializer, OrderStatusUpdateSerializer, PromoCodeSerializer


class PromoCodeListView(generics.ListCreateAPIView):
    """
    Allows staff to list all promo codes and add new ones from the dashboard.
    """

    queryset = PromoCode.objects.order_by("code")
    serializer_class = PromoCodeSerializer


class PromoCodeDetailView(generics.RetrieveUpdateAPIView):
    """
    Allows staff to PATCH/PUT a single promo code entry.
    """

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer


class OrderListView(generics.ListCreateAPIView):
    """
    Order feed with ability to accept new customer orders from the kiosk.
    """

    base_queryset = Order.objects.select_related("promo_code", "user").prefetch_related("items").order_by("-created_at")

    def get_queryset(self):
        queryset = self.base_queryset
        status_param = self.request.query_params.get("status")
        if status_param:
            statuses = {value.strip().upper() for value in status_param.split(",") if value.strip()}
            valid_statuses = [status for status in statuses if status in Order.Status.values]
            if valid_statuses:
                queryset = queryset.filter(status__in=valid_statuses)
            else:
                queryset = queryset.none()
        else:
            excluded = {Order.Status.FULFILLED, Order.Status.CANCELLED}
            active_statuses = [status for status in Order.Status.values if status not in excluded]
            queryset = queryset.filter(status__in=active_statuses)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user=request.user if request.user.is_authenticated else None)
        read_serializer = OrderSerializer(order, context={"request": request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrderStatusUpdateView(generics.UpdateAPIView):
    """
    Allow staff to update the status of an order from the dashboard.
    """

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = OrderSerializer(instance, context={"request": request})
        return Response(read_serializer.data)
