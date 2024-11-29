from django.shortcuts import get_object_or_404
from RestConnectApp.models import Mesa, Pedido, DetallePedido, Producto
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password  # Para encriptar la contraseña
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from RestConnectApp.models import Producto,User
from RestConnectApi.serializers import MesaSerializar,PedidoSerializar,DetallePedidoSerializar,ProductoSerializar,UsuarioSerializar


# Create your views here.



@api_view(['GET','POST'])
def MesaApi(request):
    if request.method =='GET':
        mesa = Mesa.objects.all()
        serializer =MesaSerializar(mesa,many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        serializer = MesaSerializar(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def agregar_pedido_api(request):
    """
    API para agregar un pedido nuevo junto con sus detalles.
    """
    data = request.data
    try:
        # Crear el pedido
        pedido_serializer = PedidoSerializar(data={
            "fecha_pedido": data["fecha_pedido"],
            "estado": data["estado"],
            "total": data["total"],
            "mesa": data["mesa"],
            "usuario": data["usuario"]
        })
        if pedido_serializer.is_valid():
            pedido = pedido_serializer.save()
        else:
            return Response(pedido_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar el estado de la mesa asociada
        mesa = Mesa.objects.get(id=data["mesa"])
        mesa.estado = "ocupada"
        mesa.pedido_actual = pedido  # Asociar el pedido a la mesa
        mesa.hora_ingreso = pedido.fecha_pedido
        mesa.save()

        # Agregar los detalles del pedido
        detalles = data.get("detalles", [])
        for detalle in detalles:
            detalle["pedido"] = pedido.id  # Asignar el ID del pedido creado
            detalle_serializer = DetallePedidoSerializar(data=detalle)
            if detalle_serializer.is_valid():
                detalle_serializer.save()
            else:
                return Response(detalle_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Pedido creado exitosamente."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET', 'DELETE'])
def ver_pedido_api(request, pedido_id):
    """
    API para obtener un pedido específico y sus detalles con información ampliada.
    También permite eliminar un pedido si se hace una solicitud DELETE.
    """
    try:
        # Buscar el pedido por ID
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Si es un DELETE, proceder con la eliminación
        if request.method == 'DELETE':
            # Verificar si el pedido está asociado a una mesa
            if pedido.mesa:
                mesa = pedido.mesa
                # Desasociar el pedido de la mesa
                mesa.hora_ingreso= None
                mesa.estado = 'libre'  # Actualizamos el estado de la mesa a 'libre'
                mesa.pedido_actual = None  # Desasociamos el pedido de la mesa
                mesa.save()
            
            # Eliminar el pedido
            pedido.delete()

            return Response({"message": f"Pedido {pedido_id} eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
        
        # Si es un GET, devolver los detalles del pedido
        pedido_serializer = PedidoSerializar(pedido)
        detalles = DetallePedido.objects.filter(pedido=pedido)
        detalle_serializer = DetallePedidoSerializar(detalles, many=True)

        return Response({
            "pedido": pedido_serializer.data,
            "detalles": detalle_serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def producto_api(request, producto_id=None):
    """
    API para manejar los productos:
    - GET: Listar todos los productos o un producto específico.
    - POST: Crear un nuevo producto.
    - PUT: Actualizar un producto existente.
    - DELETE: Eliminar un producto específico por ID.
    """
    if request.method == 'GET':
        if producto_id:
            # Obtener un producto específico
            producto = get_object_or_404(Producto, id=producto_id)
            serializer = ProductoSerializar(producto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Listar todos los productos
            productos = Producto.objects.all()
            serializer = ProductoSerializar(productos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Crear un nuevo producto
        serializer = ProductoSerializar(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        if producto_id:
            # Obtener el producto a actualizar
            producto = get_object_or_404(Producto, id=producto_id)
            serializer = ProductoSerializar(producto, data=request.data, partial=True)  # partial=True para permitir actualizaciones parciales
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "ID de producto necesario para actualizar"}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Eliminar un producto específico por ID
        producto = get_object_or_404(Producto, id=producto_id)
        producto.delete()
        return Response({"message": f"Producto {producto_id} eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
@api_view(['GET'])
def UsuarioApi(request, pk=None):
    # Obtener todos los usuarios (GET)
    if request.method == 'GET':
        if pk:  # Si se especifica un 'id' (pk), obtener ese usuario específico
            try:
                usuario = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            serializer = UsuarioSerializar(usuario)
            return Response(serializer.data)
        else:  # Si no se especifica un 'id', obtener la lista de todos los usuarios
            usuarios = User.objects.all()
            serializer = UsuarioSerializar(usuarios, many=True)
            return Response(serializer.data)