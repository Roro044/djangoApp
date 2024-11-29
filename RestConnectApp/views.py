from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login,logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.models import User
import logging
from django.db.models import F,Sum
from django.utils.timezone import now
from .models import Mesa, Pedido, DetallePedido,Producto
from .forms import PedidoForm, DetallePedidoForm

logger = logging.getLogger(__name__)
def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_active:
                logger.info(f"Usuario autenticado: {username}")
                auth_login(request, user)
                return redirect('inicio')
            else:
                messages.error(request, 'El usuario está inactivo. Contacta al administrador.')
        else:
            logger.warning(f"Fallo en el login: {username}")
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'AppTemplates/login.html')

@login_required
def logout_view(request):
    logout(request)  # Cierra la sesión del usuario
    return redirect('login')  # Redirige al login

@login_required
def inicio(request):
    mesas = Mesa.objects.all().order_by('numero_mesa')  # Ordenar las mesas por el número de mesa
    return render(request, 'AppTemplates/inicio.html', {
        'mesas': mesas,
        'usuario': request.user
    })
@login_required


def mesa_accion(request, mesa_id):
    """Redirige según el estado de la mesa."""
    mesa = get_object_or_404(Mesa, id=mesa_id)

    if mesa.estado == 'ocupada' and mesa.pedido_actual:
        # Si la mesa está ocupada y tiene un pedido actual, redirige al detalle del pedido
        return redirect('detalle_pedido', pedido_id=mesa.pedido_actual.id)
    
    # Si la mesa está libre, redirige a agregar pedido
    return redirect('agregar_pedido', mesa_id=mesa_id)

@login_required
@permission_required('RestConnectApp.add_pedido', raise_exception=True)
def agregar_pedido(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)

    if mesa.estado == 'ocupada' and mesa.pedido_actual:
        return redirect('detalle_pedido', pedido_id=mesa.pedido_actual.id)

    # Ordenar las mesas libres por número de mesa
    mesas_libres = Mesa.objects.filter(estado='libre').order_by('numero_mesa')
    productos = Producto.objects.all()

    if request.method == 'POST':
        # Validar la mesa seleccionada
        mesa_seleccionada_id = request.POST.get('mesa')
        if not mesa_seleccionada_id:
            messages.error(request, "Debes seleccionar una mesa.")
            return redirect('agregar_pedido', mesa_id=mesa_id)

        mesa_seleccionada = get_object_or_404(Mesa, id=mesa_seleccionada_id)

        # Validar y procesar los productos seleccionados
        productos_seleccionados_json = request.POST.get('productos')
        if not productos_seleccionados_json:
            messages.error(request, "Debes seleccionar al menos un producto.")
            return redirect('agregar_pedido', mesa_id=mesa_id)

        try:
            import json
            productos_seleccionados = json.loads(productos_seleccionados_json)
        except json.JSONDecodeError:
            messages.error(request, "Ocurrió un error al procesar los productos.")
            return redirect('agregar_pedido', mesa_id=mesa_id)

        # Crear el pedido
        pedido = Pedido.objects.create(
            mesa=mesa_seleccionada,
            usuario=request.user,
            estado="pendiente",
            total=0  # Se calculará después
        )

        # Agregar detalles del pedido
        total = 0
        for producto_id, datos in productos_seleccionados.items():
            producto = get_object_or_404(Producto, id=producto_id)
            cantidad = datos["cantidad"]
            precio_unitario = producto.precio

            # Crear el detalle
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )

            # Calcular el total
            total += precio_unitario * cantidad

        # Guardar el total en el pedido
        pedido.total = total
        pedido.save()

        # Actualizar el estado de la mesa
        mesa_seleccionada.estado = 'ocupada'
        mesa_seleccionada.pedido_actual = pedido
        mesa_seleccionada.save()

        messages.success(request, "Pedido registrado exitosamente.")
        return redirect('inicio')  # Redirige al inicio o lista de pedidos

    return render(request, 'AppTemplates/agregar_pedido.html', {
        'mesas': mesas_libres,  # Mesas ya ordenadas por número
        'productos': productos,
    })


@login_required
@permission_required('RestConnectApp.view_pedido', raise_exception=True)
def detalle_pedido(request, pedido_id):
    # Obtener el pedido por su ID
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Obtener los detalles del pedido
    detalles = DetallePedido.objects.filter(pedido=pedido)
    
    # Obtener la mesa asociada con el pedido
    mesa = pedido.mesa

    # Verificar el método POST para liberar la mesa o cerrar la comanda
    if request.method == 'POST':
        if 'liberar_mesa' in request.POST:
            # Eliminar todos los detalles del pedido
            detalles.delete()

            # Eliminar el pedido
            pedido.delete()

            # Resetear la mesa
            mesa.estado = 'libre'  # Marcar la mesa como libre
            mesa.hora_ingreso = None  # Eliminar la hora de ingreso
            mesa.pedido_actual = None  # Eliminar la relación con el pedido
            mesa.save()

            messages.success(request, f"Mesa {mesa.numero_mesa} liberada exitosamente.")
            return redirect('inicio')

        elif 'cerrar_comanda' in request.POST:
            pedido.estado = 'completado'
            pedido.save()
            messages.success(request, "Comanda cerrada correctamente.")
            return redirect('inicio')

    return render(request, 'AppTemplates/detalle_pedido.html', {
        'pedido': pedido,
        'detalles': detalles,
        'mesa': mesa  # Asegúrate de pasar la mesa al contexto
    })


@login_required
def desocupar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    mesa.estado = 'libre'
    mesa.hora_ingreso = None
    mesa.pedido_actual = None
    mesa.save()

    messages.success(request, f"La Mesa {mesa.numero_mesa} ahora está libre.")
    return redirect('inicio')


@login_required
def cerrar_comanda(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Cambiar el estado del pedido a "completado"
    pedido.estado = 'completado'
    pedido.save()

    # Actualizar la mesa asociada
    mesa = pedido.mesa
    mesa.estado = 'libre'  # La mesa se libera al cerrar la comanda
    mesa.pedido_actual = None  # Se elimina el pedido actual

    # Restablecer el total de la mesa a 0
    mesa.total = 0
    mesa.save()

    # Actualizar el contador de cuentas cobradas en el reporte
    cuentas_cobradas = Pedido.objects.filter(estado='completado').count()

    # Redirigir al inicio con mensaje de éxito
    messages.success(request, f"Comanda cerrada correctamente. Total de cuentas cobradas: {cuentas_cobradas}")
    return redirect('inicio')  # Redirigir a la vista de reporte de ventas


def obtener_mesas(request):
    mesas = list(Mesa.objects.values())
    return JsonResponse(mesas, safe=False)


def seleccionar_mesa(request, mesa_id):
    # Buscar la mesa
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    # Comprobar si ya hay un pedido asociado a esta mesa
    pedido = Pedido.objects.filter(mesa=mesa).first()

    if pedido:
        # Si ya existe un pedido, redirigir a su detalle
        return redirect('detalle_pedido', pk=pedido.pk)
    else:
        # Si no hay pedido, ir a la vista para agregar un nuevo pedido
        return redirect('agregar_pedido')  # Asegúrate de que tienes esta vista configurada

@login_required
def liberar_mesa(request, mesa_id):
    # Verifica si el usuario tiene el permiso
    if not request.user.has_perm('app_name.can_liberar_mesa'):  # Cambia 'app_name' por el nombre correcto de la app
        return redirect('login')  # Redirige al login si no tiene el permiso

    # Obtiene la mesa por su id
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == "POST":
        # Si hay un pedido asociado, se elimina
        if mesa.pedido_actual:
            pedido = mesa.pedido_actual
            pedido.delete()
        
        # Resetea los valores de la mesa
        mesa.estado = 'libre'
        mesa.garzon = None
        mesa.hora_ingreso = None
        mesa.pedido_actual = None
        mesa.save()
        
        messages.success(request, f"La mesa {mesa.numero_mesa} ha sido liberada.")
        return redirect('inicio')
    
    return render(request, 'AppTemplates/confirmar_liberar_mesa.html', {'mesa': mesa})

@login_required
def reporte_ventas(request):
    # Verifica si el usuario tiene el permiso
    if not request.user.has_perm('app_name.can_ver_reporte_ventas'):  # Cambia 'app_name' por el nombre correcto de la app
        return redirect('login')  # Redirige al login si no tiene el permiso

    # Si tiene el permiso, continúa con la vista
    cuentas_totales = Mesa.objects.count()
    cuentas_abiertas = Mesa.objects.filter(estado='ocupada').count()
    cuentas_pendientes = Pedido.objects.filter(estado='pendiente').count()
    cuentas_cobradas = Pedido.objects.filter(estado='completado').count()

    # Totales de ventas
    venta_total = sum([mesa.total() for mesa in Mesa.objects.all()])
    venta_abierta = sum([pedido.total for pedido in Pedido.objects.filter(estado='pendiente')])
    venta_pendiente = sum([pedido.total for pedido in Pedido.objects.filter(estado='pendiente')])
    venta_cobrada = sum([pedido.total for pedido in Pedido.objects.filter(estado='completado')])

    # Venta total = Venta cobradas + Venta abierta
    venta_total_actualizada = venta_cobrada + venta_abierta

    context = {
        'cuentas_totales': cuentas_totales,
        'cuentas_abiertas': cuentas_abiertas,
        'cuentas_pendientes': cuentas_pendientes,
        'cuentas_cobradas': cuentas_cobradas,
        'venta_total': venta_total_actualizada,  # Se actualiza la venta total
        'venta_abierta': venta_abierta,
        'venta_pendiente': venta_pendiente,
        'venta_cobrada': venta_cobrada,
    }

    return render(request, 'AppTemplates/reporte_ventas.html', context)