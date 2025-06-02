from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication 
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import serializers

from .models import EquipmentType, Equipment
from .serializers import (
    EquipmentTypeSerializer,
    EquipmentListSerializer,
    EquipmentCreateSerializer,
    EquipmentUpdateSerializer
)

class EquipmentTypeViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для типов оборудования.
    Поддерживает:
    - GET (список, пагинация, поиск по имени, фильтрация по id)
    - GET (получение id)
    - POST (создание)
    - PUT (обновление по id)
    - DELETE (удаление по id)
    """
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'name']
    search_fields = ['name', 'serial_number_mask']
    ordering_fields = ['id', 'name']

    def list(self, request, *args, **kwargs):
        """
        Вывод пагинированного списка типов оборудования
        с возможностью поиска путем указания query параметров.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Запрос данных по id."""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Создание новой записи."""
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Редактирование записи."""
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Частичное редактирование записи."""
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Удаление записи."""
        # Прежде чем удалять тип, можно добавить проверку, не используется ли он оборудованием
        instance = self.get_object()
        if instance.equipments.filter(is_deleted=False).exists():
            return Response(
                {"detail": "Нельзя удалить тип оборудования, так как он используется активным оборудованием."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для оборудования.
    Поддерживает:
    - GET (список, пагинация, поиск по серийному номеру/примечанию, фильтр по equipment_type_id)
    - GET (получение по id)
    - POST (создать одно или несколько)
    - PUT (обновить по id)
    - DELETE (мягкое удаление по id)
    """
    serializer_class = EquipmentListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Для фильтрации по ID типа оборудования: /api/equipment/?equipment_type__id=1
    # Или по имени типа: /api/equipment/?equipment_type__name=TP-Link
    filterset_fields = {
        'equipment_type__id': ['exact'],
        'equipment_type__name': ['exact', 'icontains'],
        'serial_number': ['exact', 'icontains'],
        'note': ['icontains'],
        'is_deleted': ['exact'] # Позволит фильтровать и удаленные, если нужно /api/equipment/?is_deleted=true
    }
    search_fields = ['serial_number', 'note', 'equipment_type__name']
    ordering_fields = ['id', 'serial_number', 'equipment_type__name']

    def get_queryset(self):
        """
        Переопределяем queryset, чтобы по умолчанию показывать только не удаленное оборудование.
        """
        show_deleted = self.request.query_params.get('is_deleted')
        if show_deleted == 'true':
            return Equipment.objects.all().select_related('equipment_type')
        if show_deleted == 'all':
            return Equipment.objects.all().select_related('equipment_type')
        return Equipment.objects.filter(is_deleted=False).select_related('equipment_type')

    def get_serializer_class(self):
        """
        Разные сериализаторы для разных действий.
        """
        if self.action == 'create':
            return EquipmentCreateSerializer
        if self.action in ['update', 'partial_update']:
            return EquipmentUpdateSerializer
        return EquipmentListSerializer # Для list, retrieve

    def create(self, request, *args, **kwargs):
        """
        Создание новой(ых) записи(ей) оборудования.
        Может принимать как один объект, так и массив объектов для пакетного создания.
        В ТЗ указано "на входе json-массив" для создания коллекции,
        но DRF по умолчанию ожидает один объект.
        Если всегда json-массив, то нужно many=True в сериализаторе или кастомная обработка.
        EquipmentCreateSerializer уже ожидает serial_numbers как список.
        Если сам запрос POST /api/equipment может быть массивом объектов:
        [{"equipment_type_id": 1, "serial_numbers": ["SN1"], "note": "N1"},
         {"equipment_type_id": 1, "serial_numbers": ["SN2"], "note": "N2"}]
        Тогда сериализатор для create должен иметь many=True.

        Текущий EquipmentCreateSerializer ожидает ОДИН объект запроса,
        в котором `serial_numbers` это список.
        Пример запроса:
        POST /api/equipment/
        {
            "equipment_type_id": 1,
            "serial_numbers": ["SN001", "SN002", "SN003"],
            "note": "Test batch"
        }
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.save() # create метод сериализатора вернет dict
            # result = {"created_equipment": [...], "errors": [...]}
            # Определяем статус ответа в зависимости от наличия ошибок
            response_data = result
            status_code = status.HTTP_201_CREATED
            if result.get("errors"):
                if result.get("created_equipment"):
                    status_code = status.HTTP_207_MULTI_STATUS
                else: # Только ошибки
                    status_code = status.HTTP_400_BAD_REQUEST
            elif not result.get("created_equipment"): # Нет созданных и нет ошибок (странно, но возможно)
                 status_code = status.HTTP_204_NO_CONTENT


            return Response(response_data, status=status_code)

        except serializers.ValidationError as e:
            # Если валидация в сериализаторе упала до вызова .save()
            # или .save() поднял ValidationError с ошибками
            error_detail = e.detail
            # Если это наш кастомный ValidationError из create со списком ошибок
            if isinstance(error_detail, dict) and "errors" in error_detail:
                return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
            # Иначе, стандартная ошибка валидации DRF
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)





    def destroy(self, request, *args, **kwargs):
        """
        Мягкое удаление записи.
        """
        instance = self.get_object()
        if instance.is_deleted:
            return Response({"detail": "Оборудование уже было удалено."}, status=status.HTTP_400_BAD_REQUEST)
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    def list(self, request, *args, **kwargs):
        """
        Вывод пагинированного списка оборудования
        с возможностью поиска путем указания query параметров.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Запрос данных по id."""
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Редактирование записи."""
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Частичное редактирование записи."""
        return super().partial_update(request, *args, **kwargs)