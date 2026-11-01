// =====================================================================
// JSON Schema de todas las colecciones del concesionario.
// Se ejecuta DESPUÉS de "python manage.py migrate":
//
//     mongosh concesionario_app json_schema/validaciones.js
//
// Cada colección queda "blindada": Mongo rechaza cualquier documento que
// no cumpla la estructura, aunque se inserte por fuera de Django.
// Los nombres de los campos son los mismos de los modelos (snake_case),
// porque así es como Djongo los guarda.
// =====================================================================

const NUMERO = ['double', 'int', 'long'];
const ENTERO = ['int', 'long'];
const CORREO = '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$';
const CORREO_OPCIONAL = '^$|^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$';

// Campos que Djongo agrega a todos los documentos
const BASE = {
    _id: { bsonType: 'objectId', description: 'Identificador interno de Mongo' },
    id: { bsonType: ENTERO, minimum: 1, description: 'Identificador autoincremental de Django' },
};

// ---------- Objetos embebidos que se repiten en varias colecciones ----------

const CLIENTE_RESUMEN = {
    bsonType: 'object',
    description: 'Copia mínima del cliente (colección clientes)',
    required: ['documento', 'nombre_completo', 'telefono', 'email'],
    additionalProperties: false,
    properties: {
        documento: { bsonType: 'string', minLength: 5, maxLength: 20 },
        nombre_completo: { bsonType: 'string', minLength: 3, maxLength: 200 },
        telefono: { bsonType: 'string', minLength: 1, maxLength: 20 },
        email: { bsonType: 'string', pattern: CORREO_OPCIONAL },
    },
};

const VEHICULO_RESUMEN = {
    bsonType: 'object',
    description: 'Copia mínima del vehículo (colección vehiculos)',
    required: ['placa', 'marca', 'modelo', 'anio'],
    additionalProperties: false,
    properties: {
        placa: { bsonType: 'string', pattern: '^[A-Z0-9-]{3,10}$' },
        marca: { bsonType: 'string', minLength: 1, maxLength: 50 },
        modelo: { bsonType: 'string', minLength: 1, maxLength: 50 },
        anio: { bsonType: ENTERO, minimum: 1950, maximum: 2030 },
    },
};

const USUARIO_RESUMEN = {
    bsonType: 'object',
    description: 'Copia mínima del asesor (colección usuarios)',
    required: ['nombre_usuario', 'nombre_completo'],
    additionalProperties: false,
    properties: {
        nombre_usuario: { bsonType: 'string', minLength: 1, maxLength: 150 },
        nombre_completo: { bsonType: 'string', minLength: 3, maxLength: 200 },
    },
};

// ---------- Esquemas por colección ----------

const esquemas = {

    roles: {
        bsonType: 'object',
        title: 'Rol',
        required: ['_id', 'id', 'nombre', 'descripcion', 'permisos', 'fecha_creacion'],
        additionalProperties: false,
        properties: {
            ...BASE,
            nombre: { bsonType: 'string', minLength: 1, maxLength: 50 },
            descripcion: { bsonType: 'string', maxLength: 200 },
            permisos: {
                bsonType: 'array',
                description: 'Lista de permisos embebidos',
                items: {
                    bsonType: 'object',
                    required: ['modulo', 'nivel'],
                    additionalProperties: false,
                    properties: {
                        modulo: { enum: ['usuarios', 'clientes', 'historial', 'ventas', 'pagos'] },
                        nivel: { enum: ['lectura', 'escritura', 'total'] },
                    },
                },
            },
            fecha_creacion: { bsonType: 'date' },
        },
    },

    usuarios: {
        bsonType: 'object',
        title: 'Usuario',
        required: ['_id', 'id', 'nombre_usuario', 'contrasena', 'nombre', 'apellido', 'email', 'telefono',
                   'cargo', 'activo', 'rol', 'fecha_creacion', 'fecha_actualizacion'],
        additionalProperties: false,
        properties: {
            ...BASE,
            nombre_usuario: { bsonType: 'string', minLength: 3, maxLength: 150 },
            contrasena: { bsonType: 'string', minLength: 20, description: 'Contraseña cifrada (hash)' },
            nombre: { bsonType: 'string', minLength: 1, maxLength: 100 },
            apellido: { bsonType: 'string', minLength: 1, maxLength: 100 },
            email: { bsonType: 'string', pattern: CORREO },
            telefono: { bsonType: 'string', maxLength: 20 },
            cargo: { enum: ['administrador', 'vendedor', 'cajero', 'tecnico', 'gerente'] },
            activo: { bsonType: 'bool' },
            rol: {
                bsonType: ['object', 'null'],
                description: 'Rol embebido (copia de la colección roles)',
                required: ['nombre', 'descripcion'],
                additionalProperties: false,
                properties: {
                    nombre: { bsonType: 'string', minLength: 1, maxLength: 50 },
                    descripcion: { bsonType: 'string', maxLength: 200 },
                },
            },
            fecha_creacion: { bsonType: 'date' },
            fecha_actualizacion: { bsonType: 'date' },
        },
    },

    clientes: {
        bsonType: 'object',
        title: 'Cliente',
        required: ['_id', 'id', 'tipo_documento', 'documento', 'nombre', 'apellido', 'email', 'telefono',
                   'fecha_nacimiento', 'direccion', 'fecha_registro'],
        additionalProperties: false,
        properties: {
            ...BASE,
            tipo_documento: { enum: ['CC', 'CE', 'NIT', 'PAS'] },
            documento: { bsonType: 'string', minLength: 5, maxLength: 20 },
            nombre: { bsonType: 'string', minLength: 1, maxLength: 100 },
            apellido: { bsonType: 'string', minLength: 1, maxLength: 100 },
            email: { bsonType: 'string', pattern: CORREO_OPCIONAL },
            telefono: { bsonType: 'string', minLength: 1, maxLength: 20 },
            fecha_nacimiento: { bsonType: ['date', 'null'] },
            direccion: {
                bsonType: ['object', 'null'],
                description: 'Dirección embebida',
                required: ['ciudad', 'barrio', 'calle'],
                additionalProperties: false,
                properties: {
                    ciudad: { bsonType: 'string', minLength: 1, maxLength: 60 },
                    barrio: { bsonType: 'string', maxLength: 60 },
                    calle: { bsonType: 'string', minLength: 1, maxLength: 120 },
                },
            },
            fecha_registro: { bsonType: 'date' },
        },
    },

    vehiculos: {
        bsonType: 'object',
        title: 'Vehiculo',
        required: ['_id', 'id', 'placa', 'marca', 'modelo', 'anio', 'color', 'tipo', 'condicion', 'precio',
                   'kilometraje', 'estado', 'imagen_url', 'descripcion', 'ficha_tecnica', 'fecha_ingreso'],
        additionalProperties: false,
        properties: {
            ...BASE,
            placa: { bsonType: 'string', pattern: '^[A-Z0-9-]{3,10}$' },
            marca: { bsonType: 'string', minLength: 1, maxLength: 50 },
            modelo: { bsonType: 'string', minLength: 1, maxLength: 50 },
            anio: { bsonType: ENTERO, minimum: 1950, maximum: 2030 },
            color: { bsonType: 'string', minLength: 1, maxLength: 30 },
            tipo: { enum: ['sedan', 'hatchback', 'suv', 'camioneta', 'pickup', 'deportivo'] },
            condicion: { enum: ['nuevo', 'usado'] },
            precio: { bsonType: NUMERO, minimum: 0 },
            kilometraje: { bsonType: ENTERO, minimum: 0 },
            estado: { enum: ['disponible', 'reservado', 'vendido'] },
            imagen_url: { bsonType: 'string', pattern: '^$|^https?://' },
            descripcion: { bsonType: 'string' },
            ficha_tecnica: {
                bsonType: ['object', 'null'],
                description: 'Ficha técnica embebida',
                required: ['motor', 'cilindraje', 'transmision', 'combustible', 'puertas'],
                additionalProperties: false,
                properties: {
                    motor: { bsonType: 'string', minLength: 1, maxLength: 50 },
                    cilindraje: { bsonType: ENTERO, minimum: 0 },
                    transmision: { enum: ['manual', 'automatica'] },
                    combustible: { enum: ['gasolina', 'diesel', 'hibrido', 'electrico'] },
                    puertas: { bsonType: ENTERO, minimum: 2, maximum: 6 },
                },
            },
            fecha_ingreso: { bsonType: 'date' },
        },
    },

    talleres: {
        bsonType: 'object',
        title: 'Taller',
        required: ['_id', 'id', 'nombre', 'nit', 'telefono', 'ciudad', 'especialidad', 'fecha_registro'],
        additionalProperties: false,
        properties: {
            ...BASE,
            nombre: { bsonType: 'string', minLength: 1, maxLength: 100 },
            nit: { bsonType: 'string', minLength: 1, maxLength: 20 },
            telefono: { bsonType: 'string', minLength: 1, maxLength: 20 },
            ciudad: { bsonType: 'string', minLength: 1, maxLength: 60 },
            especialidad: { enum: ['general', 'electrico', 'latoneria', 'llantas', 'concesionario'] },
            fecha_registro: { bsonType: 'date' },
        },
    },

    historiales: {
        bsonType: 'object',
        title: 'HistorialVehiculo',
        required: ['_id', 'id', 'vehiculo', 'observaciones', 'propietarios_anteriores', 'mantenimientos',
                   'fecha_creacion'],
        additionalProperties: false,
        properties: {
            ...BASE,
            vehiculo: VEHICULO_RESUMEN,
            observaciones: { bsonType: 'string' },
            propietarios_anteriores: {
                bsonType: 'array',
                items: {
                    bsonType: 'object',
                    required: ['nombre', 'documento', 'fecha_inicio', 'fecha_fin'],
                    additionalProperties: false,
                    properties: {
                        nombre: { bsonType: 'string', minLength: 1, maxLength: 150 },
                        documento: { bsonType: 'string', maxLength: 20 },
                        fecha_inicio: { bsonType: 'date' },
                        fecha_fin: { bsonType: 'date' },
                    },
                },
            },
            mantenimientos: {
                bsonType: 'array',
                items: {
                    bsonType: 'object',
                    required: ['tipo', 'descripcion', 'fecha', 'kilometraje', 'costo', 'taller'],
                    additionalProperties: false,
                    properties: {
                        tipo: { enum: ['cambio_aceite', 'frenos', 'llantas', 'revision_general', 'electrico',
                                       'latoneria', 'otro'] },
                        descripcion: { bsonType: 'string', maxLength: 300 },
                        fecha: { bsonType: 'date' },
                        kilometraje: { bsonType: ENTERO, minimum: 0 },
                        costo: { bsonType: NUMERO, minimum: 0 },
                        taller: { bsonType: 'string', minLength: 1, maxLength: 100 },
                    },
                },
            },
            fecha_creacion: { bsonType: 'date' },
        },
    },

    cotizaciones: {
        bsonType: 'object',
        title: 'Cotizacion',
        required: ['_id', 'id', 'numero', 'cliente', 'vehiculo', 'vendedor', 'precio_base', 'descuento_porcentaje',
                   'precio_ofertado', 'fecha', 'vigencia_dias', 'estado', 'notas'],
        additionalProperties: false,
        properties: {
            ...BASE,
            numero: { bsonType: 'string', pattern: '^COT-[0-9]{4,}$' },
            cliente: CLIENTE_RESUMEN,
            vehiculo: VEHICULO_RESUMEN,
            vendedor: USUARIO_RESUMEN,
            precio_base: { bsonType: NUMERO, minimum: 0 },
            descuento_porcentaje: { bsonType: NUMERO, minimum: 0, maximum: 30 },
            precio_ofertado: { bsonType: NUMERO, minimum: 0 },
            fecha: { bsonType: 'date' },
            vigencia_dias: { bsonType: ENTERO, minimum: 1, maximum: 90 },
            estado: { enum: ['pendiente', 'aprobada', 'rechazada', 'vendida'] },
            notas: { bsonType: 'string' },
        },
    },

    ventas: {
        bsonType: 'object',
        title: 'Venta',
        required: ['_id', 'id', 'numero', 'numero_cotizacion', 'cliente', 'vehiculo', 'vendedor', 'precio_final',
                   'forma_pago', 'fecha_venta', 'estado', 'facturada', 'observaciones'],
        additionalProperties: false,
        properties: {
            ...BASE,
            numero: { bsonType: 'string', pattern: '^VEN-[0-9]{4,}$' },
            numero_cotizacion: { bsonType: 'string', pattern: '^$|^COT-[0-9]{4,}$' },
            cliente: CLIENTE_RESUMEN,
            vehiculo: VEHICULO_RESUMEN,
            vendedor: USUARIO_RESUMEN,
            precio_final: { bsonType: NUMERO, minimum: 0 },
            forma_pago: { enum: ['contado', 'credito', 'leasing'] },
            fecha_venta: { bsonType: 'date' },
            estado: { enum: ['activa', 'anulada'] },
            facturada: { bsonType: 'bool' },
            observaciones: { bsonType: 'string' },
        },
    },

    facturas: {
        bsonType: 'object',
        title: 'Factura',
        required: ['_id', 'id', 'numero_factura', 'numero_venta', 'fecha_emision', 'fecha_vencimiento', 'cliente',
                   'vehiculo', 'subtotal', 'iva_porcentaje', 'impuesto_iva', 'total', 'estado', 'pagos'],
        additionalProperties: false,
        properties: {
            ...BASE,
            numero_factura: { bsonType: 'string', pattern: '^FAC-[0-9]{4,}$' },
            numero_venta: { bsonType: 'string', pattern: '^VEN-[0-9]{4,}$' },
            fecha_emision: { bsonType: 'date' },
            fecha_vencimiento: { bsonType: 'date' },
            cliente: CLIENTE_RESUMEN,
            vehiculo: VEHICULO_RESUMEN,
            subtotal: { bsonType: NUMERO, minimum: 0 },
            iva_porcentaje: { bsonType: NUMERO, minimum: 0, maximum: 50 },
            impuesto_iva: { bsonType: NUMERO, minimum: 0 },
            total: { bsonType: NUMERO, minimum: 0 },
            estado: { enum: ['pendiente', 'pagada', 'anulada'] },
            pagos: {
                bsonType: 'array',
                description: 'Pagos embebidos dentro de la factura',
                items: {
                    bsonType: 'object',
                    required: ['tipo_pago', 'forma_pago', 'monto', 'fecha_pago', 'numero_referencia', 'observaciones'],
                    additionalProperties: false,
                    properties: {
                        tipo_pago: { enum: ['efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'cheque'] },
                        forma_pago: { enum: ['contado', 'cuota'] },
                        monto: { bsonType: NUMERO, minimum: 1 },
                        fecha_pago: { bsonType: 'date' },
                        numero_referencia: { bsonType: 'string', maxLength: 50 },
                        observaciones: { bsonType: 'string', maxLength: 300 },
                    },
                },
            },
        },
    },
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
