from django.contrib import admin

from .models import MovimientoInventario, Pedido, PiezaSolicitada, Producto, ProductoProveedor, Proveedor


class CotizacionInline(admin.TabularInline):
    model = ProductoProveedor
    extra = 2
    max_num = ProductoProveedor.MAXIMO  # dos proveedores por producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'marca', 'precio_venta', 'costo_pedido', 'stock', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'codigo', 'marca')
    inlines = [CotizacionInline]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'proveedor', 'cantidad', 'precio_unit', 'costo_total', 'fecha')
    readonly_fields = ('costo_total',)


@admin.register(MovimientoInventario)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'cantidad', 'stock_resultante', 'motivo')
    list_filter = ('tipo',)


admin.site.register(Proveedor)
admin.site.register(PiezaSolicitada)
