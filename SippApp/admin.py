from django.contrib import admin
from .models import (
    Cliente, EmpresaProveedora, CategoriaProducto,
    ProductoHardware, CaracteristicaProductoHardware,
    ServicioInformatico, TipoServicio, Pedido,
    ItemProductoPedido, ItemServicioPedido
)
# Register your models here.

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'encargado', 'presupuesto',
        'email_contacto', 'fecha_vencimiento_presupuesto',
        'presupuesto_vencido'
    ]
    list_filter = ['fecha_vencimiento_presupuesto']
    search_fields = ['nombre', 'encargado', 'email_contacto']
    readonly_fields = ['presupuesto_vencido']


@admin.register(EmpresaProveedora)
class EmpresaProveedoraAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'encargado']
    search_fields = ['nombre', 'encargado']


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class CaracteristicaProductoHardwareInline(admin.TabularInline):
    """Inline para las características de productos de hardware"""
    model = CaracteristicaProductoHardware
    extra = 1
    fields = ['attr', 'valor']

@admin.register(ProductoHardware)
class ProductoHardwareAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo', 'categoria', 'precio',
        'empresa_proveedora'
    ]
    list_filter = ['tipo', 'categoria', 'empresa_proveedora']
    search_fields = ['nombre', 'caracteristicas__attr', 'caracteristicas__valor']
    inlines = [CaracteristicaProductoHardwareInline]

    def get_queryset(self, request):
        """Optimizar queries para las características"""
        return super().get_queryset(request).prefetch_related('caracteristicas')

@admin.register(CaracteristicaProductoHardware)
class CaracteristicaProductoHardwareAdmin(admin.ModelAdmin):
    list_display = ['attr', 'valor', 'producto_hardware']
    list_filter = ['attr', 'producto_hardware__tipo']
    search_fields = ['attr', 'valor', 'producto_hardware__nombre']

class TipoServicioInline(admin.TabularInline):
    """Inline para los tipos de servicio"""
    model = TipoServicio
    extra = 1
    fields = ['tipo']

@admin.register(ServicioInformatico)
class ServicioInformaticoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'duracion_completa', 'precio',
        'empresa_proveedora', 'activo'
    ]
    list_filter = ['empresa_proveedora', 'activo', 'unidad_duracion']
    search_fields = ['nombre', 'descripcion', 'observaciones']
    inlines = [TipoServicioInline]
    readonly_fields = ['duracion_completa']

@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'servicio']
    list_filter = ['servicio__empresa_proveedora']
    search_fields = ['tipo', 'servicio__nombre']


class ItemProductoPedidoInline(admin.TabularInline):
    """Inline para productos en pedidos"""
    model = ItemProductoPedido
    extra = 1
    readonly_fields = ['precio_unitario', 'subtotal']

    def get_queryset(self, request):
        """Optimizar queries para productos"""
        return super().get_queryset(request).select_related('productos')


class ItemServicioPedidoInline(admin.TabularInline):
    """Inline para servicios en pedidos"""
    model = ItemServicioPedido
    extra = 1
    readonly_fields = ['precio_unitario', 'subtotal']

    def get_queryset(self, request):
        """Optimizar queries para servicios"""
        return super().get_queryset(request).select_related('servicio')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cliente', 'fecha_pedido', 'estado',
        'total_pedido'
    ]
    list_filter = ['estado', 'fecha_pedido']
    search_fields = [
        'cliente__nombre',
        'observaciones',
        'items_productos__producto__nombre',
        'items_servicios__servicio__nombre'
    ]
    inlines = [ItemProductoPedidoInline, ItemServicioPedidoInline]
    readonly_fields = ['fecha_pedido', 'total_pedido']

    def get_queryset(self, request):
        """Optimizar queries para calcular el total"""
        return super().get_queryset(request).prefetch_related(
            'items_productos',
            'items_servicios'
        )


@admin.register(ItemProductoPedido)
class ItemProductoPedidoAdmin(admin.ModelAdmin):
    list_display = [
        'pedido', 'producto', 'cantidad',
        'precio_unitario', 'subtotal'
    ]
    list_filter = ['pedido__estado', 'producto__tipo']
    search_fields = ['pedido__cliente__nombre', 'producto__nombre']
    readonly_fields = ['subtotal']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'pedido', 'pedido__cliente', 'productos'
        )


@admin.register(ItemServicioPedido)
class ItemServicioPedidoAdmin(admin.ModelAdmin):
    list_display = [
        'pedido', 'servicio', 'cantidad',
        'precio_unitario', 'subtotal'
    ]
    list_filter = ['pedido__estado', 'servicio__empresa_proveedora']
    search_fields = ['pedido__cliente__nombre', 'servicio__nombre']
    readonly_fields = ['subtotal']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'pedido', 'pedido__cliente', 'servicio'
        )


# Configuración del sitio admin opcional
admin.site.site_header = "Sistema de Gestión de Pedidos Informáticos"
admin.site.site_title = "Sistema Pedidos"
admin.site.index_title = "Administración del Sistema"