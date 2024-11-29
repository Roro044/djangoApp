from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password



class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
    ]
    numero_mesa = models.IntegerField(unique=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='libre')
    garzon = models.CharField(max_length=100, blank=True, null=True)
    hora_ingreso = models.DateTimeField(blank=True, null=True)
    pedido_actual = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True, blank=True, related_name='mesa_actual')

    @property

    def delete(self, *args, **kwargs):
        # Restablecer la mesa asociada
        self.mesa.estado = 'libre'
        self.mesa.hora_ingreso = None
        self.mesa.pedido_actual = None
        
        # Recalcular el total de la mesa
        self.mesa.total = 0  # Reseteamos el total
        self.mesa.save()  # Guardamos los cambios en la mesa
        
        # Ahora eliminamos el pedido
        super().delete(*args, **kwargs)
    def total(self):
        # Calcular dinámicamente el total sumando el total de todos los pedidos
        total = 0
        for pedido in self.pedido_set.filter(estado='pendiente'):  # Solo sumar los pedidos pendientes
            total += pedido.total
        return total
    def __str__(self):
        return f"Mesa {self.numero_mesa} - {self.estado}"

class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('Bebida', 'Bebida'),
        ('Comida', 'Comida'),
        ('Postre', 'Postre'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ]
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(default=now)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Si el pedido cambia a completado, actualizamos el estado de la mesa y creamos un reporte de ventas
        if self.estado == 'pendiente':
            self.mesa.estado = 'ocupada'
            self.mesa.hora_ingreso = now()
        elif self.estado == 'completado':
            self.mesa.estado = 'libre'
            self.mesa.hora_ingreso = None
            self.mesa.save()

            # Crear el reporte de ventas cuando se completa el pedido
            self.crear_reporte_ventas()

        super().save(*args, **kwargs)

    def crear_reporte_ventas(self):
        # Crear un reporte de ventas para este pedido
        reporte = ReporteVentas.objects.create(
            fecha_reporte=now().date(),
            total_ventas=self.total,
            pedido=self
        )
        # Puedes añadir más lógica para incluir productos más vendidos, etc.
        return reporte


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle {self.id} - Pedido {self.pedido.id}"
    

class ReporteVentas(models.Model):
    fecha_reporte = models.DateField(auto_now_add=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    productos_mas_vendidos = models.TextField(blank=True, null=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='reportes', blank=True, null=True)

    def __str__(self):
        return f"Reporte {self.fecha_reporte}"

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField()
    numero_personas = models.IntegerField()
    mesa_asignada = models.CharField(max_length=100, blank=True, null=True)
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)

    def __str__(self):
        return f"Reserva {self.usuario.username} - {self.fecha_reserva}"


class Inventario(models.Model):
    fecha = models.DateField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    inventario_col = models.IntegerField()

    def __str__(self):
        return f"Inventario {self.fecha} - {self.producto.nombre}"