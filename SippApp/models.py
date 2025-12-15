from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Cliente(models.Model):
    """Modelo para almacenar la información de los clientes"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre del cliente")
    encargado = models.CharField(max_length=200, verbose_name="Persona encargada")
    presupuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Presupuesto disponible",
        validators=[MinValueValidator(0)]
    )
    email_contacto = models.EmailField(verbose_name="Email de contacto")
    fecha_vencimiento_presupuesto = models.DateField(verbose_name="Fecha de vencimiento del presupuesto")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.encargado}"

    @property
    def presupuesto_vencido(self):
        """Verifica si el presupuesto está vencido"""
        return timezone.now().date() > self.fecha_vencimiento_presupuesto


class EmpresaProveedora(models.Model):
    """Modelo para almacenar las empresas proveedoras"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    encargado = models.CharField(max_length=200, verbose_name="Persona encargada")

    class Meta:
        verbose_name = "Empresa Proveedora"
        verbose_name_plural = "Empresas Proveedoras"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.encargado}"


class CategoriaProducto(models.Model):
    """Categorías para los productos de hardware"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"

    def __str__(self):
        return self.nombre


class ProductoHardware(models.Model):
    """Modelo para los productos de hardware"""
    TIPO_PRODUCTO_CHOICES = [
        ('switch', 'Switch'),
        ('disco_duro', 'Disco Duro'),
        ('ram', 'RAM'),
        ('impresora', 'Impresora'),
        ('teclado', 'Teclado'),
        ('mouse', 'Mouse'),
        ('ordenador', 'Ordenador'),
        ('laptop', 'Laptop'),
        ('otros', 'Otros'),
    ]
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del productos"
    )
    tipo = models.CharField(
        max_length=100,
        choices=TIPO_PRODUCTO_CHOICES,
        default='otros',
        verbose_name="Tipo de productos (selección)"
    )
    tipo_personalizado = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tipo personalizado (si selecciona 'Otros')"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio",
        validators=[MinValueValidator(0)]
    )
    empresa_proveedora = models.ForeignKey(
        EmpresaProveedora,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name="Empresa Proveedora",
        null=True,
        blank=True,
    )
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.CASCADE,
        verbose_name="Categoría",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True, verbose_name="Producto disponible")

    class Meta:
        verbose_name = "Producto de Hardware"
        verbose_name_plural = "Productos de Hardware"
        ordering = ['tipo', 'nombre']
        unique_together = ['nombre', 'empresa_proveedora']

    @property
    def tipo_seleccion(self):
        """Propiedad que devuelve el tipo final"""
        if self.tipo == 'otros' and self.tipo_personalizado:
            return self.tipo_personalizado
        return self.get_tipo_display()

    def __str__(self):
        return f"{self.nombre} -  (${self.precio})"

    def clean(self):
        """Validación personalizada"""
        from django.core.exceptions import ValidationError

        if self.tipo == 'otros' and not self.tipo_personalizado:
            raise ValidationError({
                'tipo_personalizado': 'Debe especificar un tipo personalizado cuando selecciona "Otros"'
            })


class CaracteristicaProductoHardware(models.Model):
    attr = models.CharField(max_length=100)
    valor = models.CharField(max_length=200)
    producto_hardware = models.ForeignKey(
        ProductoHardware,
        on_delete=models.CASCADE,
        related_name='caracteristicas',
        verbose_name="Producto de Hardware"
    )

    class Meta:
        verbose_name = "Caracteristica de Producto de Hardware"

    def __str__(self):
        return f"{self.attr} - {self.valor}"


class ServicioInformatico(models.Model):
    """Modelo para los servicios informáticos"""
    UNIDAD_DURACION_CHOICES = [
        ('horas', 'Horas'),
        ('dias', 'Días'),
        ('meses', 'Meses'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre del servicio")
    duracion = models.PositiveIntegerField(verbose_name="Duración del servicio")
    unidad_duracion = models.CharField(
        max_length=10,
        choices=UNIDAD_DURACION_CHOICES,
        verbose_name="Unidad de duración"
    )
    descripcion = models.TextField(verbose_name="Descripción del servicio")
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio del servicio",
        validators=[MinValueValidator(0)]
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones generales")
    empresa_proveedora = models.ForeignKey(
        EmpresaProveedora,
        on_delete=models.CASCADE,
        related_name='servicios',
        verbose_name="Empresa Proveedora"
    )
    activo = models.BooleanField(default=True, verbose_name="Servicio disponible")

    class Meta:
        verbose_name = "Servicio Informático"
        verbose_name_plural = "Servicios Informáticos"
        ordering = ['nombre']
        unique_together = ['nombre', 'empresa_proveedora']

    def __str__(self):
        return f"{self.nombre} - {self.empresa_proveedora.nombre} (${self.precio})"

    @property
    def duracion_completa(self):
        return f"{self.duracion} {self.get_unidad_duracion_display()}"


class TipoServicio(models.Model):
    tipo = models.CharField(max_length=100)
    servicio = models.ForeignKey(
        ServicioInformatico,
        on_delete=models.CASCADE,
        related_name='tipos',
        verbose_name="Servicio Informatico"
    )
    class Meta:
        verbose_name = "Tipo Servicio"

    def __str__(self):
        return f"{self.tipo}"


class Pedido(models.Model):
    """Modelo para los pedidos realizados por los clientes"""
    ESTADO_PEDIDO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
        ('otros', 'Otros'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name="Cliente"
    )
    fecha_pedido = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha del pedido"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_PEDIDO_CHOICES,
        default='pendiente',
        verbose_name="Estado del pedido"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones del pedido")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre} - {self.fecha_pedido.strftime('%d/%m/%Y')}"

    @property
    def total_pedido(self):
        """Calcula el total del pedido sumando productos y servicios"""
        total_productos = sum(
            item.subtotal for item in self.items_productos.all()
        )
        total_servicios = sum(
            item.subtotal for item in self.items_servicios.all()
        )
        return total_productos + total_servicios


class ItemProductoPedido(models.Model):
    """Modelo intermedio para los productos en un pedido"""
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items_productos'
    )
    producto = models.ForeignKey(
        ProductoHardware,
        on_delete=models.CASCADE,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario"
    )

    class Meta:
        verbose_name = "Item de Producto en Pedido"
        verbose_name_plural = "Items de Productos en Pedidos"
        unique_together = ['pedido', 'producto']

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} - ${self.precio_unitario}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        # Al guardar, se almacena el precio actual del productos
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)


class ItemServicioPedido(models.Model):
    """Modelo intermedio para los servicios en un pedido"""
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items_servicios'
    )
    servicio = models.ForeignKey(
        ServicioInformatico,
        on_delete=models.CASCADE,
        verbose_name="Servicio"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario"
    )

    class Meta:
        verbose_name = "Item de Servicio en Pedido"
        verbose_name_plural = "Items de Servicios en Pedidos"
        unique_together = ['pedido', 'servicio']

    def __str__(self):
        return f"{self.cantidad} x {self.servicio.nombre} - ${self.precio_unitario}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        # Al guardar, se almacena el precio actual del servicio
        if not self.precio_unitario:
            self.precio_unitario = self.servicio.precio
        super().save(*args, **kwargs)
