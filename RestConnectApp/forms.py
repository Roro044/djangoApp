from django import forms
from .models import Pedido, DetallePedido, Mesa

class PedidoForm(forms.ModelForm):
    mesa = forms.ModelChoiceField(
        queryset=Mesa.objects.all(),
        empty_label="Seleccione una mesa",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    class Meta:
        model = Pedido
        fields = []

class DetallePedidoForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']