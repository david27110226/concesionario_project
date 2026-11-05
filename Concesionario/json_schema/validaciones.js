// =====================================================================
// JSON Schema de las colecciones del concesionario.
// Se ejecuta DESPUÉS de "python manage.py migrate":
//
//     mongosh concesionario_app json_schema/validaciones.js
//
// Colecciones: usuarios, clientes, vehiculos, plantillasCotizacion, facturas.
// Mongo rechaza cualquier documento que no cumpla la estructura, aunque se
// inserte por fuera de Django. Los nombres de los campos son los mismos de
// los modelos, porque así es como Djongo los guarda.
// =====================================================================

const NUMERO = ['double', 'int', 'long'];
const ENTERO = ['int', 'long'];
const CORREO = '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$';
const CORREO_OPCIONAL = '^$|^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$';
const PLACA = '^[A-Z0-9-]{3,10}$';

// Campos que Djongo agrega a todos los documentos
const BASE = {
    _id: { bsonType: 'objectId', description: 'Identificador interno de Mongo' },
    id: { bsonType: ENTERO, minimum: 1, description: 'Identificador autoincremental de Django' },
};

function texto(maximo, minimo = 0) {
    return { bsonType: 'string', minLength: minimo, maxLength: maximo };
}

function objeto(propiedades, requeridos, descripcion) {
    const esquema = {
        bsonType: 'object',
        required: requeridos || Object.keys(propiedades),
        additionalProperties: false,
        properties: propiedades,
    };
    if (descripcion) esquema.description = descripcion;
    return esquema;
}

function arreglo(elemento, descripcion) {
    return { bsonType: 'array', description: descripcion, items: elemento };
}

// Usuario que crea o atiende (DetalleVendedor / CreadoPor)
const PERSONA_USUARIO = objeto({
    nombre_usuario: texto(150, 1),
    nombre: texto(100, 1),
    apellido: texto(100, 1),
});

const esquemas = {

    // ---------------- gestion_usuarios ----------------
    usuarios: objeto({
        ...BASE,
        nombre_usuario: texto(150, 1),
        contrasena: texto(255, 1),
        nombre: texto(100, 1),
        apellido: texto(100, 1),
        email: { bsonType: 'string', pattern: CORREO },
        telefono: texto(20),
        es_administrador: { bsonType: 'bool' },
        es_superusuario: { bsonType: 'bool' },
        esta_activo: { bsonType: 'bool' },
        activo: { bsonType: 'bool' },
        fecha_creacion: { bsonType: 'date' },
        fecha_actualizacion: { bsonType: 'date' },
        rol: {
            bsonType: ['object', 'null'],
            description: 'Rol embebido con sus permisos por módulo',
            required: ['nombre', 'descripcion', 'perm_clientes', 'perm_ventas', 'perm_historial', 'perm_pagos', 'perm_usuarios'],
            additionalProperties: false,
            properties: {
                nombre: texto(50, 1),
                descripcion: { bsonType: 'string' },
                perm_clientes: { bsonType: 'bool' },
                perm_ventas: { bsonType: 'bool' },
                perm_historial: { bsonType: 'bool' },
                perm_pagos: { bsonType: 'bool' },
                perm_usuarios: { bsonType: 'bool' },
            },
        },
        auditoria: arreglo(objeto({
            accion: { enum: ['login', 'logout', 'crear', 'editar', 'eliminar', 'ver'] },
            modulo: texto(100, 1),
            descripcion: { bsonType: 'string' },
            ip: texto(45),
            fecha: { bsonType: 'date' },
            exitoso: { bsonType: 'bool' },
        }), 'Acciones realizadas por el usuario'),
        metas: arreglo(objeto({
            mes: { bsonType: ENTERO, minimum: 1, maximum: 12 },
            anio: { bsonType: ENTERO, minimum: 2000, maximum: 2100 },
            meta_ventas: { bsonType: ENTERO, minimum: 0 },
            ventas_realizadas: { bsonType: ENTERO, minimum: 0 },
            fecha_asignacion: { bsonType: 'date' },
        }), 'Metas mensuales de ventas'),
        notificaciones: arreglo(objeto({
            remitente: texto(150, 1),
            asunto: texto(200, 1),
            mensaje: texto(5000, 1),
            fecha: { bsonType: 'date' },
            leida: { bsonType: 'bool' },
            fecha_lectura: { bsonType: ['date', 'null'] },
        }), 'Mensajes recibidos'),
    }, null, 'Usuario del concesionario'),

    // ---------------- clientes_vehiculos ----------------
    clientes: objeto({
        ...BASE,
        nombre: texto(100, 1),
        apellido: texto(100, 1),
        cedula: { bsonType: 'string', pattern: '^[0-9]{5,20}$' },
        email: { bsonType: 'string', pattern: CORREO_OPCIONAL },
        telefono: texto(20, 1),
        direccion: { bsonType: 'string' },
        fecha_registro: { bsonType: 'date' },
        cotizaciones: arreglo(objeto({
            vehiculo: objeto({
                marca: texto(50, 1),
                modelo: texto(50, 1),
                anio: { bsonType: ENTERO, minimum: 1950, maximum: 2030 },
                placa: { bsonType: 'string', pattern: PLACA },
                precio: { bsonType: NUMERO.concat('null'), minimum: 0 },
            }, null, 'Copia del vehículo cotizado (VehiculoCotizacion)'),
            vendedor: PERSONA_USUARIO,
            precio_ofertado: { bsonType: NUMERO.concat('null'), minimum: 0 },
            fecha: { bsonType: 'date' },
            estado: { enum: ['pendiente', 'aprobada', 'rechazada'] },
            notas: { bsonType: 'string' },
            venta: {
                bsonType: ['object', 'null'],
                description: 'Venta de la cotización; la factura solo guarda su número',
                required: ['fecha_venta', 'precio_final', 'forma_pago', 'numero_factura'],
                additionalProperties: false,
                properties: {
                    fecha_venta: { bsonType: ['date', 'null'] },
                    precio_final: { bsonType: NUMERO.concat('null'), minimum: 0 },
                    forma_pago: texto(50),
                    numero_factura: texto(20),
                },
            },
        }), 'Cotizaciones del cliente'),
    }, null, 'Cliente del concesionario'),

    vehiculos: objeto({
        ...BASE,
        marca: texto(50, 1),
        modelo: texto(50, 1),
        anio: { bsonType: ENTERO, minimum: 1950, maximum: 2030 },
        color: texto(30),
        placa: { bsonType: 'string', pattern: PLACA, description: 'Única en la colección' },
        precio: { bsonType: NUMERO.concat('null'), minimum: 0 },
        kilometraje: { bsonType: ENTERO, minimum: 0 },
        estado: { enum: ['disponible', 'reservado', 'vendido'] },
        descripcion: { bsonType: 'string' },
        fecha_ingreso: { bsonType: 'date' },
        fecha_actualizacion: { bsonType: 'date' },
        propietarios_anteriores: arreglo(objeto({
            nombre: texto(100, 1),
            fecha_inicio: { bsonType: 'date' },
            fecha_fin: { bsonType: 'date' },
        }), 'Dueños anteriores del vehículo'),
        mantenimientos: arreglo(objeto({
            tipo: { enum: ['cambio_aceite', 'frenos', 'llantas', 'revision_general', 'otro'] },
            descripcion: { bsonType: 'string' },
            fecha: { bsonType: 'date' },
            costo: { bsonType: NUMERO.concat('null'), minimum: 0 },
        }), 'Mantenimientos del vehículo'),
    }, null, 'Vehículo del inventario'),

    // ---------------- ventas_cotizaciones ----------------
    plantillasCotizacion: objeto({
        ...BASE,
        nombre: texto(100, 1),
        descripcion: { bsonType: 'string' },
        activa: { bsonType: 'bool' },
        fecha_creacion: { bsonType: 'date' },
        fecha_actualizacion: { bsonType: 'date' },
        creado_por: PERSONA_USUARIO,
        condiciones: arreglo(objeto({
            titulo: texto(150, 1),
            contenido: texto(5000, 1),
            orden: { bsonType: ENTERO, minimum: 1 },
        }), 'Condiciones comerciales'),
        descuentos: arreglo(objeto({
            nombre: texto(100, 1),
            porcentaje: { bsonType: NUMERO, minimum: 0, maximum: 100 },
            descripcion: { bsonType: 'string' },
        }), 'Descuentos que se pueden aplicar al cotizar'),
        notas_adicionales: { bsonType: 'string' },
    }, null, 'Plantilla de cotización'),

    // ---------------- pagos_facturacion ----------------
    facturas: objeto({
        ...BASE,
        numero_factura: { bsonType: 'string', pattern: '^FAC-[0-9]{5}$' },
        fecha_emision: { bsonType: 'date' },
        cedula_cliente: { bsonType: 'string', pattern: '^[0-9]{5,20}$' },
        nombre_cliente: texto(150, 1),
        placa_vehiculo: { bsonType: 'string', pattern: PLACA },
        subtotal: { bsonType: NUMERO, minimum: 0 },
        impuesto_iva: { bsonType: NUMERO, minimum: 0 },
        total: { bsonType: NUMERO, minimum: 0 },
        estado: { enum: ['emitida', 'pagada', 'anulada'] },
        pagos: arreglo(objeto({
            tipo_pago: { enum: ['efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'cheque'] },
            forma_pago: { enum: ['contado', 'cuota'] },
            monto: { bsonType: NUMERO, minimum: 1 },
            fecha_pago: { bsonType: 'date' },
            numero_referencia: texto(50),
            observaciones: { bsonType: 'string' },
        }), 'Pagos recibidos'),
    }, null, 'Factura de una venta (única colección de facturas)'),
};

// ---------- Aplicar los esquemas ----------

const existentes = db.getCollectionNames();

for (const [coleccion, esquema] of Object.entries(esquemas)) {
    const opciones = {
        validator: { $jsonSchema: esquema },
        validationLevel: 'strict',
        validationAction: 'error',
    };
    if (existentes.includes(coleccion)) {
        db.runCommand({ collMod: coleccion, ...opciones });
    } else {
        db.createCollection(coleccion, opciones);
    }
    print(`JSON Schema aplicado a "${coleccion}"`);
}
