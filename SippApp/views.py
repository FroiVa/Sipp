from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from .models import (
    Cliente, EmpresaProveedora, CategoriaProducto, ProductoHardware,
    CaracteristicaProductoHardware, ServicioInformatico, TipoServicio,
    Pedido, ItemProductoPedido, ItemServicioPedido
)
from .forms import (
    ClienteForm, EmpresaProveedoraForm, ProductoHardwareForm,
    ServicioInformaticoForm, PedidoForm, ItemProductoPedidoFormSet,
    ItemServicioPedidoFormSet, ProductoSearchForm, PedidoSearchForm,
    CaracteristicaProductoHardwareFormSet
)


# ==================== VISTAS DEL DASHBOARD ====================

class DashboardView(View):
    """Vista principal del dashboard"""
    template_name = 'dashboard.html'

    def get(self, request):
        # Estadísticas generales
        total_clientes = Cliente.objects.count()
        total_pedidos = Pedido.objects.count()
        total_productos = ProductoHardware.objects.filter(activo=True).count()
        total_servicios = ServicioInformatico.objects.filter(activo=True).count()

        # Pedidos por estado
        pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
        pedidos_en_proceso = Pedido.objects.filter(estado='en_proceso').count()
        pedidos_completados = Pedido.objects.filter(estado='completado').count()

        # Clientes con presupuesto vencido
        clientes_presupuesto_vencido = Cliente.objects.filter(
            fecha_vencimiento_presupuesto__lt=timezone.now().date()
        ).count()

        # Pedidos recientes
        pedidos_recientes = Pedido.objects.select_related('cliente').order_by('-fecha_pedido')[:10]

        # Productos más vendidos
        productos_populares = ProductoHardware.objects.annotate(
            total_vendido=Sum('itemproductopedido__cantidad')
        ).filter(total_vendido__isnull=False).order_by('-total_vendido')[:5]

        # Servicios más solicitados
        servicios_populares = ServicioInformatico.objects.annotate(
            total_solicitado=Sum('itemserviciopedido__cantidad')
        ).filter(total_solicitado__isnull=False).order_by('-total_solicitado')[:5]

        context = {
            'total_clientes': total_clientes,
            'total_pedidos': total_pedidos,
            'total_productos': total_productos,
            'total_servicios': total_servicios,
            'pedidos_pendientes': pedidos_pendientes,
            'pedidos_en_proceso': pedidos_en_proceso,
            'pedidos_completados': pedidos_completados,
            'clientes_presupuesto_vencido': clientes_presupuesto_vencido,
            'pedidos_recientes': pedidos_recientes,
            'productos_populares': productos_populares,
            'servicios_populares': servicios_populares,
        }

        return render(request, self.template_name, context)


# ==================== VISTAS DE CLIENTES ====================

class ClienteListView(LoginRequiredMixin, ListView):
    """Lista de clientes con búsqueda y filtros"""
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 15

    def get_queryset(self):
        queryset = Cliente.objects.all()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(encargado__icontains=search_query) |
                Q(email_contacto__icontains=search_query)
            )

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['total_clientes'] = self.get_queryset().count()
        return context


class ClienteDetailView(LoginRequiredMixin, DetailView):
    """Detalle de cliente con sus pedidos"""
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.get_object()

        # Pedidos del cliente
        pedidos = cliente.pedidos.all().select_related(
            'cliente'
        ).prefetch_related(
            'items_productos', 'items_servicios'
        ).order_by('-fecha_pedido')

        # Estadísticas del cliente
        total_pedidos = pedidos.count()
        total_gastado = sum(pedido.total_pedido for pedido in pedidos if pedido.total_pedido)

        context.update({
            'pedidos': pedidos,
            'total_pedidos': total_pedidos,
            'total_gastado': total_gastado,
            'presupuesto_restante': cliente.presupuesto - total_gastado if total_gastado else cliente.presupuesto,
        })

        return context


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo cliente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """Editar cliente existente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar cliente"""
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Cliente eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ==================== VISTAS DE EMPRESAS PROVEEDORAS ====================

class EmpresaProveedoraListView(ListView):
    """Lista de empresas proveedoras"""
    model = EmpresaProveedora
    template_name = 'empresas/empresa_list.html'
    context_object_name = 'empresas'
    paginate_by = 15

    def get_queryset(self):
        queryset = EmpresaProveedora.objects.all()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(encargado__icontains=search_query)
            )

        return queryset.order_by('nombre')


class EmpresaProveedoraDetailView(DetailView):
    """Detalle de empresa proveedora con sus productos y servicios"""
    model = EmpresaProveedora
    template_name = 'empresas/empresa_detail.html'
    context_object_name = 'empresa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_object()

        context.update({
            'productos': empresa.productos.filter(activo=True).select_related('categoria'),
            'servicios': empresa.servicios.filter(activo=True),
            'total_productos': empresa.productos.filter(activo=True).count(),
            'total_servicios': empresa.servicios.filter(activo=True).count(),
        })

        return context


class EmpresaProveedoraCreateView(CreateView):
    """Crear nueva empresa proveedora"""
    model = EmpresaProveedora
    form_class = EmpresaProveedoraForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresas')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa proveedora creada exitosamente.')
        return super().form_valid(form)


class EmpresaProveedoraUpdateView(UpdateView):
    """Editar empresa proveedora existente"""
    model = EmpresaProveedora
    form_class = EmpresaProveedoraForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        messages.success(self.request, 'Empresa proveedora actualizada exitosamente.')
        return super().form_valid(form)


# ==================== VISTAS DE PRODUCTOS ====================

class ProductoHardwareListView(LoginRequiredMixin, ListView):
    """Lista de productos con filtros avanzados"""
    model = ProductoHardware
    template_name = 'productos/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        queryset = ProductoHardware.objects.filter(activo=True)

        # Aplicar filtros
        tipo_filter = self.request.GET.get('tipo', '')
        categoria_filter = self.request.GET.get('categoria', '')
        empresa_filter = self.request.GET.get('empresa', '')
        search_query = self.request.GET.get('search', '')

        if tipo_filter:
            queryset = queryset.filter(tipo=tipo_filter)
        if categoria_filter:
            queryset = queryset.filter(categoria_id=categoria_filter)
        if empresa_filter:
            queryset = queryset.filter(empresa_proveedora_id=empresa_filter)
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(tipo_personalizado__icontains=search_query) |
                Q(caracteristicas__attr__icontains=search_query) |
                Q(caracteristicas__valor__icontains=search_query)
            ).distinct()

        return queryset.select_related('empresa_proveedora', 'categoria').prefetch_related('caracteristicas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaProducto.objects.all()
        context['empresas'] = EmpresaProveedora.objects.all()
        context['tipos'] = ProductoHardware.TIPO_PRODUCTO_CHOICES
        context['filters'] = {
            'tipo': self.request.GET.get('tipo', ''),
            'categoria': self.request.GET.get('categoria', ''),
            'empresa': self.request.GET.get('empresa', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class ProductoHardwareDetailView(LoginRequiredMixin, DetailView):
    """Detalle completo de producto"""
    model = ProductoHardware
    template_name = 'productos/producto_detail.html'
    context_object_name = 'producto'

    def get_queryset(self):
        return ProductoHardware.objects.select_related(
            'empresa_proveedora', 'categoria'
        ).prefetch_related('caracteristicas')


class ProductoHardwareCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo producto"""
    model = ProductoHardware
    form_class = ProductoHardwareForm
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['caracteristicas_formset'] = CaracteristicaProductoHardwareFormSet(self.request.POST)
        else:
            context['caracteristicas_formset'] = CaracteristicaProductoHardwareFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        caracteristicas_formset = context['caracteristicas_formset']

        if caracteristicas_formset.is_valid():
            self.object = form.save()
            caracteristicas_formset.instance = self.object
            caracteristicas_formset.save()

            messages.success(self.request, 'Producto creado exitosamente.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


class ProductoHardwareUpdateView(LoginRequiredMixin, UpdateView):
    """Editar producto existente"""
    model = ProductoHardware
    form_class = ProductoHardwareForm
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['caracteristicas_formset'] = CaracteristicaProductoHardwareFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['caracteristicas_formset'] = CaracteristicaProductoHardwareFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        caracteristicas_formset = context['caracteristicas_formset']

        if caracteristicas_formset.is_valid():
            self.object = form.save()
            caracteristicas_formset.instance = self.object
            caracteristicas_formset.save()

            messages.success(self.request, 'Producto actualizado exitosamente.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)


# ==================== VISTAS DE SERVICIOS ====================

class ServicioInformaticoListView(LoginRequiredMixin, ListView):
    """Lista de servicios informáticos"""
    model = ServicioInformatico
    template_name = 'servicios/servicio_list.html'
    context_object_name = 'servicios'
    paginate_by = 15

    def get_queryset(self):
        queryset = ServicioInformatico.objects.filter(activo=True)
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(descripcion__icontains=search_query)
            )

        return queryset.select_related('empresa_proveedora')


class ServicioInformaticoDetailView(LoginRequiredMixin, DetailView):
    """Detalle de servicio informático"""
    model = ServicioInformatico
    template_name = 'servicios/servicio_detail.html'
    context_object_name = 'servicio'


class ServicioInformaticoCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo servicio"""
    model = ServicioInformatico
    form_class = ServicioInformaticoForm
    template_name = 'servicios/servicio_form.html'
    success_url = reverse_lazy('servicio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Servicio creado exitosamente.')
        return super().form_valid(form)


class ServicioInformaticoUpdateView(LoginRequiredMixin, UpdateView):
    """Editar servicio existente"""
    model = ServicioInformatico
    form_class = ServicioInformaticoForm
    template_name = 'servicios/servicio_form.html'
    success_url = reverse_lazy('servicio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Servicio actualizado exitosamente.')
        return super().form_valid(form)


# ==================== VISTAS DE PEDIDOS ====================

class PedidoListView(LoginRequiredMixin, ListView):
    """Lista de pedidos con filtros avanzados"""
    model = Pedido
    template_name = 'pedidos/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        queryset = Pedido.objects.all()

        # Aplicar filtros
        estado_filter = self.request.GET.get('estado', '')
        cliente_filter = self.request.GET.get('cliente', '')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')

        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)
        if cliente_filter:
            queryset = queryset.filter(cliente_id=cliente_filter)
        if fecha_desde:
            queryset = queryset.filter(fecha_pedido__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_pedido__date__lte=fecha_hasta)

        return queryset.select_related('cliente').prefetch_related(
            'items_productos', 'items_servicios'
        ).order_by('-fecha_pedido')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all()
        context['estados'] = Pedido.ESTADO_PEDIDO_CHOICES
        context['filters'] = {
            'estado': self.request.GET.get('estado', ''),
            'cliente': self.request.GET.get('cliente', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        return context


class PedidoDetailView(LoginRequiredMixin, DetailView):
    """Detalle completo de pedido"""
    model = Pedido
    template_name = 'pedidos/pedido_detail.html'
    context_object_name = 'pedido'

    def get_queryset(self):
        return Pedido.objects.select_related('cliente').prefetch_related(
            'items_productos__producto',
            'items_servicios__servicio'
        )


class PedidoCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo pedido con items"""
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['producto_formset'] = ItemProductoPedidoFormSet(self.request.POST, prefix='productos')
            context['servicio_formset'] = ItemServicioPedidoFormSet(self.request.POST, prefix='servicios')
        else:
            context['producto_formset'] = ItemProductoPedidoFormSet(prefix='productos')
            context['servicio_formset'] = ItemServicioPedidoFormSet(prefix='servicios')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        producto_formset = context['producto_formset']
        servicio_formset = context['servicio_formset']

        if producto_formset.is_valid() and servicio_formset.is_valid():
            self.object = form.save()
            producto_formset.instance = self.object
            producto_formset.save()
            servicio_formset.instance = self.object
            servicio_formset.save()

            messages.success(self.request, 'Pedido creado exitosamente.')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Por favor corrige los errores en los items del pedido.')
            return self.form_invalid(form)


class PedidoUpdateView(LoginRequiredMixin, UpdateView):
    """Editar pedido existente"""
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedido_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['producto_formset'] = ItemProductoPedidoFormSet(
                self.request.POST, instance=self.object, prefix='productos'
            )
            context['servicio_formset'] = ItemServicioPedidoFormSet(
                self.request.POST, instance=self.object, prefix='servicios'
            )
        else:
            context['producto_formset'] = ItemProductoPedidoFormSet(instance=self.object, prefix='productos')
            context['servicio_formset'] = ItemServicioPedidoFormSet(instance=self.object, prefix='servicios')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        producto_formset = context['producto_formset']
        servicio_formset = context['servicio_formset']

        if producto_formset.is_valid() and servicio_formset.is_valid():
            self.object = form.save()
            producto_formset.instance = self.object
            producto_formset.save()
            servicio_formset.instance = self.object
            servicio_formset.save()

            messages.success(self.request, 'Pedido actualizado exitosamente.')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Por favor corrige los errores en los items del pedido.')
            return self.form_invalid(form)


class PedidoEstadoUpdateView(LoginRequiredMixin, View):
    """Actualizar estado del pedido (API)"""

    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado in dict(Pedido.ESTADO_PEDIDO_CHOICES):
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido actualizado a {pedido.get_estado_display()}.')
        else:
            messages.error(request, 'Estado inválido.')

        return redirect('pedido_detail', pk=pedido.pk)


# ==================== VISTAS DE CATEGORÍAS ====================

class CategoriaProductoListView(LoginRequiredMixin, ListView):
    """Lista de categorías de productos"""
    model = CategoriaProducto
    template_name = 'categorias/categoria_list.html'
    context_object_name = 'categorias'


class CategoriaProductoCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva categoría"""
    model = CategoriaProducto
    fields = ['nombre', 'descripcion']
    template_name = 'categorias/categoria_form.html'
    success_url = reverse_lazy('categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada exitosamente.')
        return super().form_valid(form)


# ==================== VISTAS API/REST ====================

@csrf_exempt
def api_get_productos_empresa(request, empresa_id):
    """API para obtener productos de una empresa (AJAX)"""
    if request.method == 'GET':
        productos = ProductoHardware.objects.filter(
            empresa_proveedora_id=empresa_id, activo=True
        ).values('id', 'nombre', 'precio', 'tipo', 'tipo_personalizado')

        # Formatear respuesta
        productos_list = []
        for producto in productos:
            productos_list.append({
                'id': producto['id'],
                'nombre': producto['nombre'],
                'precio': str(producto['precio']),
                'tipo_final': producto['tipo_personalizado'] if producto['tipo'] == 'otros' else dict(
                    ProductoHardware.TIPO_PRODUCTO_CHOICES).get(producto['tipo'], producto['tipo'])
            })

        return JsonResponse(productos_list, safe=False)


@csrf_exempt
def api_get_servicios_empresa(request, empresa_id):
    """API para obtener servicios de una empresa (AJAX)"""
    if request.method == 'GET':
        servicios = ServicioInformatico.objects.filter(
            empresa_proveedora_id=empresa_id, activo=True
        ).values('id', 'nombre', 'precio', 'duracion', 'unidad_duracion')

        # Formatear respuesta
        servicios_list = []
        for servicio in servicios:
            servicios_list.append({
                'id': servicio['id'],
                'nombre': servicio['nombre'],
                'precio': str(servicio['precio']),
                'duracion_completa': f"{servicio['duracion']} {servicio['unidad_duracion']}"
            })

        return JsonResponse(servicios_list, safe=False)


@csrf_exempt
def api_get_precio_producto(request, producto_id):
    """API para obtener precio de producto (AJAX)"""
    if request.method == 'GET':
        producto = get_object_or_404(ProductoHardware, pk=producto_id, activo=True)
        return JsonResponse({'precio': str(producto.precio)})


@csrf_exempt
def api_get_precio_servicio(request, servicio_id):
    """API para obtener precio de servicio (AJAX)"""
    if request.method == 'GET':
        servicio = get_object_or_404(ServicioInformatico, pk=servicio_id, activo=True)
        return JsonResponse({'precio': str(servicio.precio)})


# ==================== VISTAS DE REPORTES ====================

class ReportePedidosView(LoginRequiredMixin, View):
    """Vista para generar reportes de pedidos"""
    template_name = 'reportes/reporte_pedidos.html'

    def get(self, request):
        # Filtros por defecto (último mes)
        fecha_hasta = timezone.now().date()
        fecha_desde = fecha_hasta - timedelta(days=30)

        context = {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        fecha_desde = request.POST.get('fecha_desde')
        fecha_hasta = request.POST.get('fecha_hasta')

        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Fechas inválidas.')
            return redirect('reporte_pedidos')

        # Obtener pedidos en el rango de fechas
        pedidos = Pedido.objects.filter(
            fecha_pedido__date__range=[fecha_desde, fecha_hasta]
        ).select_related('cliente').prefetch_related(
            'items_productos', 'items_servicios'
        )

        # Estadísticas
        total_pedidos = pedidos.count()
        total_ingresos = sum(pedido.total_pedido for pedido in pedidos if pedido.total_pedido)
        pedidos_por_estado = pedidos.values('estado').annotate(total=Count('id'))

        context = {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'pedidos': pedidos,
            'total_pedidos': total_pedidos,
            'total_ingresos': total_ingresos,
            'pedidos_por_estado': pedidos_por_estado,
        }

        return render(request, self.template_name, context)