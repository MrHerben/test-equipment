from django.contrib import admin
from .models import EquipmentType, Equipment

@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'serial_number_mask')
    search_fields = ('name',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment_type', 'serial_number', 'note', 'is_deleted')
    list_filter = ('equipment_type', 'is_deleted')
    search_fields = ('serial_number', 'note')
    actions = ['mark_deleted', 'mark_undeleted']

    def mark_deleted(self, request, queryset):
        queryset.update(is_deleted=True)
    mark_deleted.short_description = "Пометить как удаленные"

    def mark_undeleted(self, request, queryset):
        queryset.update(is_deleted=False)
    mark_undeleted.short_description = "Снять пометку удаленные"

    def get_queryset(self, request):
        # Показываем все записи в админке, включая "удаленные"
        return Equipment.objects.all()