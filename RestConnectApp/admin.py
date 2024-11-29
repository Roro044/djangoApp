from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Mesa, Producto, Pedido, DetallePedido, ReporteVentas, Reserva, Inventario


# Registro de modelos en el administrador de Django con list_display configurado

# El modelo Usuario ya está integrado en Django, por lo que no es necesario crear un modelo personalizado para eso
# Se puede personalizar el admin para el modelo User si es necesario
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email']  # Puedes agregar más campos si es necesario

# Puedes registrar el modelo de Usuario de Django con la clase personalizada
admin.site.unregister(User)  # Primero se desregistran para personalizarlos
admin.site.register(User, UserAdmin)  # Luego los volvemos a registrar con la configuración personalizada

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero_mesa', 'estado', 'garzon', 'hora_ingreso', 'total')
    readonly_fields = ('estado', 'hora_ingreso', 'total')  # Campos no editables

class CustomUserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un usuario nuevo
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
    


class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'precio', 'stock_actual', 'categoria']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('fecha_pedido', 'estado', 'total', 'usuario', 'mesa')

class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'producto', 'cantidad', 'precio_unitario']

class ReporteVentasAdmin(admin.ModelAdmin):
    list_display = ['fecha_reporte', 'total_ventas', 'productos_mas_vendidos', 'pedido']

class ReservaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha_reserva', 'numero_personas', 'mesa_asignada', 'mesa']

class InventarioAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'inventario_col', 'producto']

# Registrar los modelos restantes en el administrador de Django
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(DetallePedido, DetallePedidoAdmin)
admin.site.register(ReporteVentas, ReporteVentasAdmin)
admin.site.register(Reserva, ReservaAdmin)
admin.site.register(Inventario, InventarioAdmin)
