
from django.urls import path
from . import views

urlpatterns = [
    path('empresas/', views.EmpresaProveedoraListView.as_view(), name='empresas' ),
    path('empresas/<int:pk>/', views.EmpresaProveedoraDetailView.as_view(), name='empresa_detail'),
    path('empresas/crear/', views.EmpresaProveedoraCreateView.as_view(), name='empresa_create'),
    path('empresas/<int:pk>/editar/', views.EmpresaProveedoraUpdateView.as_view(), name='empresa_update'),
]