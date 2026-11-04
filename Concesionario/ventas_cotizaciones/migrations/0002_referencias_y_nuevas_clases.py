# Esta migración reemplaza las colecciones 'cotizaciones' y 'ventas' (que guardaban
# cliente, vehículo y asesor como objetos embebidos) por documentos planos que se
# relacionan por referencia. Los datos anteriores de esas dos colecciones se pierden.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ventas_cotizaciones', '0001_initial'),
        ('gestion_usuarios', '0001_initial'),
        ('clientes_vehiculos', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='Venta'),
        migrations.DeleteModel(name='Cotizacion'),
        migrations.CreateModel(
            name='Cotizacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=20, unique=True)),
                ('precio_base', models.FloatField()),
                ('descuento_porcentaje', models.FloatField(default=0)),
                ('precio_ofertado', models.FloatField()),
                ('fecha', models.DateField()),
                ('vigencia_dias', models.PositiveIntegerField(default=15)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada'), ('vendida', 'Vendida')], default='pendiente', max_length=20)),
                ('notas', models.TextField(blank=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cotizaciones', to='clientes_vehiculos.cliente')),
            ],
            options={
                'db_table': 'cotizaciones',
            },
        ),
        migrations.CreateModel(
            name='Promocion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('descripcion', models.CharField(blank=True, max_length=250)),
                ('porcentaje', models.FloatField()),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'promociones',
            },
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=20, unique=True)),
                ('precio_final', models.FloatField()),
                ('forma_pago', models.CharField(choices=[('contado', 'Contado'), ('credito', 'Crédito'), ('leasing', 'Leasing')], default='contado', max_length=20)),
                ('fecha_venta', models.DateField()),
                ('estado', models.CharField(choices=[('activa', 'Activa'), ('anulada', 'Anulada')], default='activa', max_length=20)),
                ('facturada', models.BooleanField(default=False)),
                ('observaciones', models.TextField(blank=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ventas', to='clientes_vehiculos.cliente')),
                ('cotizacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ventas', to='ventas_cotizaciones.cotizacion')),
                ('vehiculo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ventas', to='clientes_vehiculos.vehiculo')),
                ('vendedor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ventas', to='gestion_usuarios.usuario')),
            ],
            options={
                'db_table': 'ventas',
            },
        ),
        migrations.CreateModel(
            name='Seguimiento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('medio', models.CharField(choices=[('llamada', 'Llamada'), ('whatsapp', 'WhatsApp'), ('correo', 'Correo'), ('visita', 'Visita al concesionario')], default='llamada', max_length=20)),
                ('resultado', models.CharField(choices=[('interesado', 'Interesado'), ('en_proceso', 'En proceso'), ('sin_respuesta', 'Sin respuesta'), ('descartado', 'Descartado')], default='en_proceso', max_length=20)),
                ('comentario', models.CharField(max_length=300)),
                ('proxima_fecha', models.DateField(blank=True, null=True)),
                ('cotizacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seguimientos', to='ventas_cotizaciones.cotizacion')),
            ],
            options={
                'db_table': 'seguimientos',
            },
        ),
        migrations.CreateModel(
            name='Garantia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('basica', 'Básica'), ('extendida', 'Extendida'), ('motor', 'Motor y transmisión')], default='basica', max_length=20)),
                ('meses', models.PositiveIntegerField(default=12)),
                ('kilometraje_limite', models.PositiveIntegerField(default=20000)),
                ('fecha_inicio', models.DateField()),
                ('estado', models.CharField(choices=[('vigente', 'Vigente'), ('vencida', 'Vencida'), ('anulada', 'Anulada')], default='vigente', max_length=20)),
                ('cobertura', models.CharField(blank=True, max_length=300)),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='garantias', to='ventas_cotizaciones.venta')),
            ],
            options={
                'db_table': 'garantias',
            },
        ),
        migrations.CreateModel(
            name='Entrega',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_programada', models.DateField()),
                ('fecha_entrega', models.DateField(blank=True, null=True)),
                ('lugar', models.CharField(max_length=120)),
                ('estado', models.CharField(choices=[('programada', 'Programada'), ('reprogramada', 'Reprogramada'), ('entregada', 'Entregada'), ('cancelada', 'Cancelada')], default='programada', max_length=20)),
                ('observaciones', models.CharField(blank=True, max_length=300)),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entregas', to='ventas_cotizaciones.venta')),
            ],
            options={
                'db_table': 'entregas',
            },
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='promocion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cotizaciones', to='ventas_cotizaciones.promocion'),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='vehiculo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cotizaciones', to='clientes_vehiculos.vehiculo'),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='vendedor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cotizaciones', to='gestion_usuarios.usuario'),
        ),
    ]
