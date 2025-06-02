from rest_framework import serializers
from .models import EquipmentType, Equipment
from django.db import transaction

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
        created_equipment = []
        errors = []

        with transaction.atomic(): # Используем транзакцию для атомарности операции
            for sn in serial_numbers:
                # 1. Валидация по маске
                if not Equipment.validate_serial_number_by_mask(sn, equipment_type.serial_number_mask):
                    errors.append({
                        "serial_number": sn,
                        "error": f"Серийный номер '{sn}' не соответствует маске '{equipment_type.serial_number_mask}'."
                    })
                    continue

                # 2. Проверка на уникальность (тип + серийный номер) для активных записей
                if Equipment.objects.filter(equipment_type=equipment_type, serial_number=sn, is_deleted=False).exists():
                    errors.append({
                        "serial_number": sn,
                        "error": f"Оборудование с типом '{equipment_type.name}' и серийным номером '{sn}' уже существует."
                    })
                    continue

                try:
                    equipment_instance = Equipment.objects.create(
                        equipment_type=equipment_type,
                        serial_number=sn,
                        note=note
                    )
                    created_equipment.append(equipment_instance)
                except Exception as e: # Ловим другие возможные ошибки при создании
                    errors.append({
                        "serial_number": sn,
                        "error": f"Не удалось создать оборудование: {str(e)}"
                    })

        if errors:
            if created_equipment and errors: # Частичный успех
                # Это сложный случай для стандартного DRF create. View будет обрабатывать это.
                # Пока что, если есть ошибки, мы их вернем.
                # Если created_equipment пуст, то все были с ошибками.
                raise serializers.ValidationError({"errors": errors, "created_count": len(created_equipment)})
            elif errors: # Только ошибки
                 raise serializers.ValidationError({"errors": errors})


        return {"created_equipment": EquipmentListSerializer(created_equipment, many=True).data, "errors": errors}


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
        """
        Валидация данных при обновлении.
        """
        instance = self.instance

        serial_number = data.get('serial_number', instance.serial_number)
        equipment_type = data.get('equipment_type', instance.equipment_type)

        if 'serial_number' in data or 'equipment_type_id' in data: # Если меняется SN или тип
            if not Equipment.validate_serial_number_by_mask(serial_number, equipment_type.serial_number_mask):
                raise serializers.ValidationError({
                    'serial_number': f"Серийный номер '{serial_number}' не соответствует маске '{equipment_type.serial_number_mask}'."
                })

            # Проверка на уникальность, если серийный номер или тип меняется
            # Исключаем текущий объект из проверки
            query = Equipment.objects.filter(
                equipment_type=equipment_type,
                serial_number=serial_number,
                is_deleted=False
            ).exclude(pk=instance.pk)

            if query.exists():
                raise serializers.ValidationError({
                    'serial_number': f"Оборудование с типом '{equipment_type.name}' и серийным номером '{serial_number}' уже существует."
                })
        return data