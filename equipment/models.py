from django.db import models
from django.core.exceptions import ValidationError
import re

class EquipmentType(models.Model):
    """
    Модель для хранения типов оборудования.
    """
    name = models.CharField(max_length=255, verbose_name="Наименование типа")
    serial_number_mask = models.CharField(max_length=255, verbose_name="Маска серийного номера")

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        # Валидация маски серийного номера
        allowed_mask_chars = set('NAaXZ')
        if not all(char in allowed_mask_chars for char in self.serial_number_mask):
            raise ValidationError({
                'serial_number_mask': "Маска серийного номера может содержать только символы 'N', 'A', 'a', 'X', 'Z'."
            })

    class Meta:
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"

class Equipment(models.Model):
    """
    Модель для хранения оборудования.
    """
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT, related_name="equipments", verbose_name="Тип оборудования")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    note = models.TextField(blank=True, null=True, verbose_name="Примечание")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалено (мягкое удаление)")

    def __str__(self):
        return f"{self.equipment_type.name} - {self.serial_number}"

    def soft_delete(self):
        """Мягкое удаление объекта."""
        self.is_deleted = True
        self.save()

    def undelete(self):
        """Восстановление объекта после мягкого удаления."""
        self.is_deleted = False
        self.save()

    @staticmethod
    def validate_serial_number_by_mask(serial_number, mask):
        """
        Валидирует серийный номер по маске.
        N – цифра от 0 до 9;
        A – прописная буква латинского алфавита;
        a – строчная буква латинского алфавита;
        X – прописная буква латинского алфавита либо цифра от 0 до 9;
        Z – символ из списка: “-”, “_”, “@”.
        """
        if len(serial_number) != len(mask):
            return False

        pattern_map = {
            'N': r'\d',
            'A': r'[A-Z]',
            'a': r'[a-z]',
            'X': r'[A-Z0-9]',
            'Z': r'[-_@]'
        }

        regex_pattern = ""
        for char_mask in mask:
            regex_pattern += pattern_map[char_mask] 

        regex_pattern = f"^{regex_pattern}$" # Исправил логику, теперь строгое соответствие всей строки

        return bool(re.match(regex_pattern, serial_number))

    def clean(self):
        """
        Кастомная валидация для модели.
        Вызывается перед сохранением в админке или при вызове full_clean().
        """
        super().clean()
        # Валидация серийного номера по маске типа оборудования
        if self.equipment_type and self.serial_number:
            if not Equipment.validate_serial_number_by_mask(self.serial_number, self.equipment_type.serial_number_mask):
                raise ValidationError({
                    'serial_number': f"Серийный номер '{self.serial_number}' не соответствует маске '{self.equipment_type.serial_number_mask}' для типа '{self.equipment_type.name}'."
                })

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        # Уникальность серийного номера в связке с типом оборудования
        # Учитываем только не удаленные записи для уникальности
        constraints = [
            models.UniqueConstraint(fields=['equipment_type', 'serial_number'],
                                    condition=models.Q(is_deleted=False),
                                    name='unique_equipment_type_serial_number_if_not_deleted')
        ]