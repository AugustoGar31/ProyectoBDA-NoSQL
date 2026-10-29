# Relacional vs. Documental: ¿cómo decido qué base de datos usar?

**Base de Datos Aplicada — Material de apoyo para el Trabajo Práctico Integrador (MongoDB)**

## Por qué este documento

Ya tienen experiencia con bases de datos relacionales (MySQL): tablas, filas, columnas, claves foráneas, `JOIN`. Ahora van a trabajar con MongoDB, una base de datos **documental**. No es "lo mismo pero con otra sintaxis" — es un modelo distinto, pensado para resolver problemas distintos.

Antes de diseñar la base del TP integrador, necesitan poder justificar **por qué** el modelo documental tiene sentido para el dominio que eligieron (eso es literalmente un punto de la consigna, sección 4). Esta guía les da el criterio concreto para hacerlo.

---

## El criterio: 5 preguntas, no una moneda al aire

No existe un "ganador universal" entre relacional y documental. La decisión depende de **cómo la aplicación va a usar los datos**. Para cada pregunta, pregúntense cuál respuesta describe mejor su dominio.

### 1. ¿Cuál es la consulta más frecuente?

| Si la consulta típica es... | Conviene... |
|---|---|
| "Traeme **todo** sobre esta entidad de una sola vez" (un pedido completo con sus ítems, un producto con todas sus especificaciones, un perfil de usuario) | **Documental** — un solo documento, una sola lectura |
| "Combiná y filtrá información de **muchas entidades relacionadas**, con reportes transversales" (ej. "todos los pagos vencidos de clientes con más de 3 pedidos en mora") | **Relacional** — para eso están los `JOIN` y el álgebra relacional |

Esta es la regla que ya vimos en el deck: **primero describir el patrón de acceso, después elegir el modelo que lo representa de forma natural** — no al revés.

### 2. ¿Los registros tienen siempre los mismos campos?

| Situación | Conviene... |
|---|---|
| Todos los registros de una entidad tienen exactamente los mismos atributos, con tipos estrictos | **Relacional** — un esquema fijo es más simple de mantener ahí |
| Los atributos varían según el tipo de instancia (un producto "ropa" tiene talle y color; uno "electrónica" tiene RAM y SSD; ninguno de los dos tiene los atributos del otro) | **Documental** — cada documento trae solo los campos que le corresponden, sin columnas vacías ni tablas de atributos genéricas |

### 3. ¿Qué tan importante es la integridad referencial?

MongoDB **no controla integridad referencial**. Si en un documento guardás una referencia (un ID) a otra colección, y ese documento referenciado se borra, Mongo no te avisa ni lo impide — queda a cargo de la aplicación.

| Situación | Conviene... |
|---|---|
| El dominio depende de reglas de integridad estrictas entre muchas tablas (no puede existir un pago sin una factura, no puede existir una factura sin un cliente válido, y el motor debe garantizarlo) | **Relacional** — `FOREIGN KEY`, `CHECK`, `UNIQUE` resuelven esto en el motor |
| Alcanza con que la aplicación valide las referencias antes de escribir | **Documental** es viable |

### 4. ¿Necesito transacciones complejas entre múltiples entidades?

| Situación | Conviene... |
|---|---|
| Pagos, reservas, movimientos contables con reglas ACID estrictas sobre muchas tablas a la vez | **Relacional** — ACID es su garantía de origen |
| Alcanza con que la atomicidad se resuelva **dentro de un solo documento** (ej. un pedido con sus ítems embebidos: todo se guarda o nada se guarda, porque es una sola escritura) | **Documental**, sin necesidad de transacciones multidocumento |

### 5. ¿Cómo es el volumen, la velocidad y la variedad de los datos?

Volumen muy grande, escritura constante a alta velocidad, datos heterogéneos, necesidad de escalar horizontalmente entre varios servidores → empujan hacia NoSQL/documental. Si ninguno de estos factores está presente, un relacional bien indexado suele alcanzar y sobrar.

---

## Un mismo dominio, modelado de las dos formas

Tomemos **gestión de pedidos** (uno de los dominios sugeridos en la consigna del TP) y veamos cómo se ve en cada modelo.

### Modelo relacional (lo que ya conocen)

```sql
CREATE TABLE cliente (
    id_cliente INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE pedido (
    id_pedido INT PRIMARY KEY AUTO_INCREMENT,
    id_cliente INT,
    fecha DATE,
    estado VARCHAR(20),
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
);

CREATE TABLE detalle_pedido (
    id_detalle INT PRIMARY KEY AUTO_INCREMENT,
    id_pedido INT,
    id_producto INT,
    cantidad INT,
    precio_unitario DECIMAL(10,2),
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido),
    FOREIGN KEY (id_producto) REFERENCES producto(id_producto)
);
```

Para ver un pedido completo con sus ítems, necesitan un `JOIN` entre tres tablas. La integridad (no puede haber un ítem sin pedido, no puede haber un pedido sin cliente) la garantiza el motor con `FOREIGN KEY`.

### Modelo documental (MongoDB)

```json
{
  "_id": "ObjectId('6710a1...')",
  "cliente": {
    "id": "ObjectId('66ff02...')",
    "nombre": "Ana Pérez",
    "email": "ana@correo.com"
  },
  "fecha": "ISODate('2026-10-15')",
  "estado": "confirmado",
  "items": [
    { "producto": "Mouse", "cantidad": 2, "precio_unitario": 25.00 },
    { "producto": "Teclado", "cantidad": 1, "precio_unitario": 75.00 }
  ],
  "total": 125.00
}
```

Acá el pedido completo (cliente + ítems) se trae con **una sola lectura**, sin `JOIN`. Se embebió `cliente` (porque al pedido le alcanza con un resumen, no necesita toda la ficha del cliente) y se embebieron los `items` (porque siempre se consultan junto con el pedido y no tiene sentido administrarlos por separado). Nadie te impide, por error de la aplicación, guardar un `items` vacío o un cliente mal cargado — eso es el costo de no tener integridad referencial automática.

### ¿Cuál es "mejor"?

Ninguna. Si el sistema necesita además generar reportes contables cruzando pedidos, pagos, facturas y stock con reglas estrictas → el relacional probablemente sigue siendo mejor opción ahí. Si la aplicación es sobre todo "mostrame el pedido de un cliente, rápido, completo, en una consulta" → el documental es más natural. **Por eso la consigna del TP les pide justificar la elección, no las dos)**, no copiar el modelo relacional en formato JSON.

---

## Checklist para la sección 4 de su TP

Antes de entregar la propuesta de dominio, respondan por escrito estas 5 preguntas aplicadas a su propio proyecto:

- [ ] ¿Cuál es la consulta más frecuente de mi dominio? ¿Pide "todo de una entidad" o "cruces entre muchas"?
- [ ] ¿Mis entidades principales tienen siempre los mismos campos, o varían según el tipo?
- [ ] ¿Qué tan grave sería que la integridad referencial no esté garantizada por el motor?
- [ ] ¿Tengo alguna operación que *necesite* ser atómica entre varios documentos, o alcanza con atomicidad dentro de un documento?
- [ ] ¿Hay algo de volumen, velocidad o variedad en mis datos que justifique NoSQL más allá de la consigna?

Si al menos 3 de estas 5 respuestas apuntan hacia "documental", tienen una justificación sólida para la sección 4. Si la mayoría apunta hacia "relacional", igual pueden avanzar con MongoDB (es el requisito del TP), pero díganlo honestamente en el informe: es information valiosa reconocer el trade-off, no ocultarlo.

---

## Para recordar

> **Primero el patrón de acceso. Después el modelo que lo represente de la forma más natural.**

No se diseña la base de datos y después se ve cómo se consulta. Se analiza cómo se va a consultar, y a partir de ahí se decide la estructura.
