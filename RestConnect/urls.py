from django.contrib import admin
from django.urls import path
from RestConnectApp import views as vista
from RestConnectApi import views as vistasApi



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vista.login, name='login'),  # Aquí estamos usando vista.login
    path('logout/', vista.logout_view, name='logout'),
    path('inicio/', vista.inicio, name='inicio'),
    path('mesa/<int:mesa_id>/accion/', vista.mesa_accion, name='mesa_accion'),
    path('liberar_mesa/<int:mesa_id>/', vista.liberar_mesa, name='liberar_mesa'),
    path('pedido/agregar/<int:mesa_id>/', vista.agregar_pedido, name='agregar_pedido'),
    path('pedido/<int:pedido_id>/detalle/', vista.detalle_pedido, name='detalle_pedido'),
    path('cerrar_comanda/<int:pedido_id>/', vista.cerrar_comanda, name='cerrar_comanda'),
    path('api/mesas/', vista.obtener_mesas, name='api_mesas'),
    path('mesa/<int:mesa_id>/', vista.seleccionar_mesa, name='seleccionar_mesa'),
    path('reporte_ventas/', vista.reporte_ventas, name='reporte_ventas'),

    #Rutas Api RestFul
    path('MesaApi/',vistasApi.MesaApi,name='MesaApi'),
    path('api/pedido/agregar/', vistasApi.agregar_pedido_api, name='agregar_pedido_api'),
    path('api/pedido/<int:pedido_id>/', vistasApi.ver_pedido_api, name='ver_pedido_api'),
    path('api/productos/', vistasApi.producto_api, name='producto_list_api'),  # Listar todos los productos
    path('api/productos/<int:producto_id>/', vistasApi.producto_api, name='producto_detail_api'),  # Producto específico
    path('api/usuarios/', vistasApi.UsuarioApi, name='listar_usuarios'),  # Para obtener todos los usuarios o crear uno nuevo
    path('api/usuarios/<int:pk>/', vistasApi.UsuarioApi, name='usuario_detalle'),  # Para obtener, actualizar o eliminar un usuario específico
        # Rutas para obtener el token JWT


]