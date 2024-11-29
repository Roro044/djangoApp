from rest_framework import serializers
from RestConnectApp.models import Mesa, Producto, Pedido, DetallePedido, User


class UsuarioSerializar(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']

    def create(self, validated_data):
        # Crear usuario con contraseña
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)  # Asegura que la contraseña se encripte antes de guardarla
            user.save()
        return user

    def update(self, instance, validated_data):
        # Actualizar usuario con nueva contraseña (si se proporciona)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Encriptar la nueva contraseña
        instance.save()
        return instance

class MesaSerializar(serializers.ModelSerializer):
    numero_mesa = serializers.IntegerField()  # Asegurándonos de que se incluya el número de la mesa.

    class Meta:
        model = Mesa
        fields = ['id', 'numero_mesa', 'estado','total','garzon']  # Incluye el número de la mesa y el estado.


class ProductoSerializar(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock_actual', 'categoria']

class PedidoSerializar(serializers.ModelSerializer):
    # Usar PrimaryKeyRelatedField para aceptar IDs en lugar de diccionarios
    mesa = serializers.PrimaryKeyRelatedField(queryset=Mesa.objects.all(), write_only=True)
    usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    mesa_info = MesaSerializar(source='mesa', read_only=True)  # Información ampliada para respuestas
    usuario_info = UsuarioSerializar(source='usuario', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'fecha_pedido', 'estado', 'total', 'mesa', 'usuario', 'mesa_info', 'usuario_info']
class DetallePedidoSerializar(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all(), write_only=True)
    producto_info = ProductoSerializar(source='producto', read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'cantidad', 'precio_unitario', 'producto', 'producto_info']