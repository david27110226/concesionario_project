from django.contrib import admin

from .models import Cotizacion, Entrega, Garantia, Promocion, Seguimiento, Venta

admin.site.register([Cotizacion, Venta, Promocion, Seguimiento, Entrega, Garantia])
