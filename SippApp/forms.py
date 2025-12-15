from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import (
    Cliente, EmpresaProveedora, CategoriaProducto, ProductoHardware,
    CaracteristicaProductoHardware, ServicioInformatico, TipoServicio,
    Pedido, ItemProductoPedido, ItemServicioPedido
)


# ==================== FORMULARIOS PRINCIPALES ====================

class ClienteForm(forms.ModelForm):
    """Formulario para Clientes"""

    class Meta:
        model = Cliente
        fields = ['nombre', 'encargado', 'presupuesto', 'email_contacto', 'fecha_vencimiento_presupuesto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente...'
            }),
            'encargado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona encargada...'
            }),
            'presupuesto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'email_contacto': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@ejemplo.com'
            }),
            'fecha_vencimiento_presupuesto': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'nombre': 'Nombre del Cliente',
            'encargado': 'Persona Encargada',
            'presupuesto': 'Presupuesto Disponible',
            'email_contacto': 'Email de Contacto',
            'fecha_vencimiento_presupuesto': 'Fecha de Vencimiento del Presupuesto',
        }

    def clean_presupuesto(self):
        """Validación personalizada para el presupuesto"""
        presupuesto = self.cleaned_data.get('presupuesto')
        if presupuesto and presupuesto < 0:
            raise ValidationError('El presupuesto no puede ser negativo.')
        return presupuesto


class EmpresaProveedoraForm(forms.ModelForm):
    """Formulario para Empresas Proveedoras"""

    class Meta:
        model = EmpresaProveedora
        fields = ['nombre', 'encargado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa...'
            }),
            'encargado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona encargada...'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Empresa',
            'encargado': 'Persona Encargada',
        }


class CategoriaProductoForm(forms.ModelForm):
    """Formulario para Categorías de Productos"""

    class Meta:
        model = CategoriaProducto
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría...'
            }),
        }


class ProductoHardwareForm(forms.ModelForm):
    """Formulario para Productos de Hardware con validación dinámica"""

    class Meta:
        model = ProductoHardware
        fields = [
            'nombre', 'tipo', 'tipo_personalizado', 'precio',
            'empresa_proveedora', 'categoria', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto...'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo'
            }),
            'tipo_personalizado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Especificar tipo personalizado...',
                'id': 'id_tipo_personalizado'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'empresa_proveedora': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'tipo_personalizado': 'Tipo Personalizado',
            'activo': 'Producto Disponible',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar las opciones de manera más amigable
        self.fields['empresa_proveedora'].queryset = EmpresaProveedora.objects.all().order_by('nombre')
        self.fields['categoria'].queryset = CategoriaProducto.objects.all().order_by('nombre')

        # Hacer que tipo_personalizado no sea requerido inicialmente
        self.fields['tipo_personalizado'].required = False

    def clean(self):
        """Validación personalizada para el tipo personalizado"""
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        tipo_personalizado = cleaned_data.get('tipo_personalizado')

        if tipo == 'otros' and not tipo_personalizado:
            self.add_error('tipo_personalizado',
                           'Debe especificar un tipo personalizado cuando selecciona "Otros"')

        if tipo != 'otros' and tipo_personalizado:
            # Limpiar el tipo personalizado si no se seleccionó "otros"
            cleaned_data['tipo_personalizado'] = ''

        return cleaned_data

    def clean_precio(self):
        """Validación del precio"""
        precio = self.cleaned_data.get('precio')
        if precio and precio <= 0:
            raise ValidationError('El precio debe ser mayor a cero.')
        return precio


class CaracteristicaProductoHardwareForm(forms.ModelForm):
    """Formulario para Características de Productos"""

    class Meta:
        model = CaracteristicaProductoHardware
        fields = ['attr', 'valor']
        widgets = {
            'attr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Atributo (ej: Memoria, Capacidad)...'
            }),
            'valor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valor (ej: 8GB, 1TB)...'
            }),
        }
        labels = {
            'attr': 'Característica',
            'valor': 'Valor',
        }


class ServicioInformaticoForm(forms.ModelForm):
    """Formulario para Servicios Informáticos"""

    class Meta:
        model = ServicioInformatico
        fields = [
            'nombre', 'duracion', 'unidad_duracion', 'descripcion',
            'precio', 'observaciones', 'empresa_proveedora', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del servicio...'
            }),
            'duracion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'unidad_duracion': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del servicio...'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
            'empresa_proveedora': forms.Select(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'activo': 'Servicio Disponible',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa_proveedora'].queryset = EmpresaProveedora.objects.all().order_by('nombre')

    def clean_precio(self):
        """Validación del precio"""
        precio = self.cleaned_data.get('precio')
        if precio and precio <= 0:
            raise ValidationError('El precio debe ser mayor a cero.')
        return precio

    def clean_duracion(self):
        """Validación de la duración"""
        duracion = self.cleaned_data.get('duracion')
        if duracion and duracion <= 0:
            raise ValidationError('La duración debe ser mayor a cero.')
        return duracion


class TipoServicioForm(forms.ModelForm):
    """Formulario para Tipos de Servicio"""

    class Meta:
        model = TipoServicio
        fields = ['tipo']
        widgets = {
            'tipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de servicio...'
            }),
        }


class PedidoForm(forms.ModelForm):
    """Formulario para Pedidos"""

    class Meta:
        model = Pedido
        fields = ['cliente', 'estado', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_cliente_pedido'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del pedido...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nombre')


# ==================== FORMSETS PARA ITEMS DE PEDIDOS ====================

class ItemProductoPedidoForm(forms.ModelForm):
    """Formulario individual para items de productos en pedidos"""

    class Meta:
        model = ItemProductoPedido
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-control select-producto',
                'data-empresa-field': 'id_empresa_proveedora'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cantidad',
                'min': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio',
                'step': '0.01',
                'min': '0',
                'readonly': 'readonly'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo productos activos
        self.fields['producto'].queryset = ProductoHardware.objects.filter(activo=True).order_by('nombre')

    def clean_cantidad(self):
        """Validación de la cantidad"""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad < 1:
            raise ValidationError('La cantidad debe ser al menos 1.')
        return cantidad


class ItemServicioPedidoForm(forms.ModelForm):
    """Formulario individual para items de servicios en pedidos"""

    class Meta:
        model = ItemServicioPedido
        fields = ['servicio', 'cantidad', 'precio_unitario']
        widgets = {
            'servicio': forms.Select(attrs={
                'class': 'form-control select-servicio',
                'data-empresa-field': 'id_empresa_proveedora'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cantidad',
                'min': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio',
                'step': '0.01',
                'min': '0',
                'readonly': 'readonly'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo servicios activos
        self.fields['servicio'].queryset = ServicioInformatico.objects.filter(activo=True).order_by('nombre')

    def clean_cantidad(self):
        """Validación de la cantidad"""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad < 1:
            raise ValidationError('La cantidad debe ser al menos 1.')
        return cantidad


# ==================== FORMSETS FACTORY ====================

# Formset para productos en pedidos
ItemProductoPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemProductoPedido,
    form=ItemProductoPedidoForm,
    fields=('producto', 'cantidad', 'precio_unitario'),
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Formset para servicios en pedidos
ItemServicioPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemServicioPedido,
    form=ItemServicioPedidoForm,
    fields=('servicio', 'cantidad', 'precio_unitario'),
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Formset para características de productos
CaracteristicaProductoHardwareFormSet = inlineformset_factory(
    ProductoHardware,
    CaracteristicaProductoHardware,
    form=CaracteristicaProductoHardwareForm,
    fields=('attr', 'valor'),
    extra=1,
    can_delete=True,
    min_num=0
)

# Formset para tipos de servicio
TipoServicioFormSet = inlineformset_factory(
    ServicioInformatico,
    TipoServicio,
    form=TipoServicioForm,
    fields=('tipo',),
    extra=1,
    can_delete=True,
    min_num=0
)


# ==================== FORMULARIOS DE BÚSQUEDA ====================

class ProductoSearchForm(forms.Form):
    """Formulario de búsqueda para productos"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar productos...'
        })
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + ProductoHardware.TIPO_PRODUCTO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        required=False,
        queryset=CategoriaProducto.objects.all(),
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PedidoSearchForm(forms.Form):
    """Formulario de búsqueda para pedidos"""
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + Pedido.ESTADO_PEDIDO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cliente = forms.ModelChoiceField(
        required=False,
        queryset=Cliente.objects.all(),
        empty_label='Todos los clientes',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ClienteSearchForm(forms.Form):
    """Formulario de búsqueda para clientes"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar clientes...'
        })
    )


# ==================== FORMULARIOS ESPECIALES ====================

class PedidoCompletoForm(forms.Form):
    """Formulario combinado para crear pedidos completos"""
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones del pedido...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nombre')