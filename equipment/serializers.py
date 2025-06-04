from rest_framework import serializers
from .models import EquipmentType, Equipment

class EquipmentTypeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Тип оборудования.
    """
    class Meta:
        model = EquipmentType
        fields = ['id', 'name', 'serial_number_mask']


class EquipmentListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка оборудования (с представлением типа оборудования).
    """
    equipment_type = EquipmentTypeSerializer(read_only=True)
    equipment_type_id = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.all(), source='equipment_type', write_only=True
    )

    class Meta:
        model = Equipment
        fields = ['id', 'equipment_type', 'equipment_type_id', 'serial_number', 'note', 'is_deleted']
        read_only_fields = ['is_deleted']


class EquipmentCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания одной или нескольких записей оборудования.
    Принимает либо один объект, либо массив объектов.
    """
    equipment_type_id = serializers.IntegerField()
    serial_numbers = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False
    )
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_equipment_type_id(self, value):
        """Проверяет существование типа оборудования."""
        if not EquipmentType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Указанный тип оборудования не существует.")
        return value

    def create(self, validated_data):
        equipment_type_id = validated_data['equipment_type_id']
        serial_numbers = validated_data['serial_numbers']
        note = validated_data.get('note')

        equipment_type = EquipmentType.objects.get(id=equipment_type_id)
        
        created_instances = []
        error_list = []

        for sn in serial_numbers: # Убрал transaction.atomic()
            # 1. Валидация по маске
            if not Equipment.validate_serial_number_by_mask(sn, equipment_type.serial_number_mask):
                error_list.append({
                    "serial_number": sn,
                    "error": f"Серийный номер '{sn}' не соответствует маске '{equipment_type.serial_number_mask}'."
                })
                continue

            # 2. Проверка на уникальность (тип + серийный номер) для активных записей
            if Equipment.objects.filter(equipment_type=equipment_type, serial_number=sn, is_deleted=False).exists():
                error_list.append({
                    "serial_number": sn,
                    "error": f"Оборудование с типом '{equipment_type.name}' и серийным номером '{sn}' уже существует."
                })
                continue

            try:
                # Каждое создание Equipment.objects.create() теперь выполняется в своей собственной транзакции
                # (если AUTOCOMMIT=True в настройках БД, что является поведением по умолчанию Django).
                equipment_instance = Equipment.objects.create(
                    equipment_type=equipment_type,
                    serial_number=sn,
                    note=note
                )
                created_instances.append(equipment_instance)
            except Exception as e: # Ловим другие возможные ошибки при создании (например, проблемы с БД)
                error_list.append({
                    "serial_number": sn,
                    "error": f"Не удалось создать оборудование '{sn}': {str(e)}"
                })
        
        
        return {
            "created_instances": EquipmentListSerializer(created_instances, many=True).data,
            "errors": error_list
        }


class EquipmentUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления оборудования.
    """
    # Запрещаем изменение типа оборудования и серийного номера через этот сериализатор.
    equipment_type_id = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.all(),
        source='equipment_type',
        required=False 
    )
    serial_number = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = Equipment
        fields = ['id', 'equipment_type_id', 'serial_number', 'note']
        read_only_fields = ['id']

    def validate(self, data):
        instance = self.instance
        serial_number = data.get('serial_number', instance.serial_number)
        equipment_type_obj = data.get('equipment_type', instance.equipment_type)

        if 'serial_number' in data or 'equipment_type' in data: # Если меняется SN или тип
            if not Equipment.validate_serial_number_by_mask(serial_number, equipment_type_obj.serial_number_mask):
                raise serializers.ValidationError({
                    'serial_number': f"Серийный номер '{serial_number}' не соответствует маске '{equipment_type_obj.serial_number_mask}'."
                })
            # Проверка на уникальность, если серийный номер или тип меняется
            # Исключаем текущий объект из проверки
            query = Equipment.objects.filter(
                equipment_type=equipment_type_obj,
                serial_number=serial_number,
                is_deleted=False
            ).exclude(pk=instance.pk)
            if query.exists():
                raise serializers.ValidationError({
                    'serial_number': f"Оборудование с типом '{equipment_type_obj.name}' и серийным номером '{serial_number}' уже существует."
                })
        return data