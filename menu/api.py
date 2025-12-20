from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MenuCategory, MenuItem
from .serializers import MenuCategorySerializer, MenuItemSerializer

class MenuView(APIView):
    def get(self, request):
        qs = MenuCategory.objects.prefetch_related("items").order_by("sort_order", "name")
        return Response(MenuCategorySerializer(qs, many=True).data)


class MenuItemDetailView(generics.UpdateAPIView):
    """
    Allows partial updates (PATCH) on individual menu items from the dashboard.
    """

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
