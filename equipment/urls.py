from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipmentTypeViewSet, EquipmentViewSet


router = DefaultRouter()
router.register(r'equipment-type', EquipmentTypeViewSet, basename='equipmenttype')
router.register(r'equipment', EquipmentViewSet, basename='equipment')

urlpatterns = [
    path('', include(router.urls)),
]