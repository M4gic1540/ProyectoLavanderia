# Documentación API Users

## Resumen
API REST para gestión de usuarios usando `django.contrib.auth.models.User`.

Métodos soportados:
- Colección: `GET`, `POST`
- Elemento: `GET`, `PUT`, `DELETE`

## Base URL
Asumiendo servidor local:
- `http://127.0.0.1:8000`

Prefijo configurado en proyecto:
- `api/v1/users`

## Documentación automática (drf-spectacular)
- Schema OpenAPI (JSON): `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc UI: `/api/docs/redoc/`

## Endpoints

### 1) Listar usuarios
- Método: `GET`
- URL: `/api/v1/users`
- Respuesta exitosa: `200 OK`

#### Ejemplo de respuesta
```json
[
  {
    "id": 1,
    "username": "jdoe",
    "email": "jdoe@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
]
```

Notas:
- Campo `password` no se expone (`write_only`).

---

### 2) Crear usuario
- Método: `POST`
- URL: `/api/v1/users`
- Respuesta exitosa: `201 Created`
- Error validación: `400 Bad Request`

#### Body esperado
```json
{
  "username": "jdoe",
  "email": "jdoe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "StrongPassword123"
}
```

#### Reglas de validación
- `email`: obligatorio, formato válido, único.
- `first_name`: obligatorio.
- `last_name`: obligatorio.
- `password`: obligatorio para creación.

#### Ejemplo de respuesta exitosa
```json
{
  "id": 1,
  "username": "jdoe",
  "email": "jdoe@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Ejemplo de error (`email` duplicado)
```json
{
  "email": [
    "Este correo electrónico ya está registrado."
  ]
}
```

---

### 3) Obtener usuario por ID
- Método: `GET`
- URL (actual): `/api/v1/users{id}/`
- Ejemplo: `/api/v1/users1/`
- Respuesta exitosa: `200 OK`
- No encontrado: `404 Not Found`

#### Ejemplo de respuesta
```json
{
  "id": 1,
  "username": "jdoe",
  "email": "jdoe@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Ejemplo de error `404`
```json
{
  "error": "Usuario con ID 99 no encontrado."
}
```

---

### 4) Actualizar usuario por ID
- Método: `PUT`
- URL (actual): `/api/v1/users{id}/`
- Respuesta exitosa: `200 OK`
- Error validación: `400 Bad Request`
- No encontrado: `404 Not Found`

#### Body de ejemplo
```json
{
  "username": "jdoe_updated",
  "email": "jdoe_new@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "AnotherStrongPassword456"
}
```

Notas:
- Si `password` llega en request, se guarda cifrado con `set_password`.
- Validación de `email` único excluye usuario actual en actualización.

---

### 5) Eliminar usuario por ID
- Método: `DELETE`
- URL (actual): `/api/v1/users{id}/`
- Respuesta exitosa: `204 No Content`
- No encontrado: `404 Not Found`
- Error interno: `500 Internal Server Error`

#### Respuesta actual al eliminar
```json
{
  "message": "Usuario con ID 1 eliminado correctamente."
}
```

Nota:
- Aunque se retorna `204`, implementación devuelve cuerpo JSON. En HTTP estricto, `204` debería ir sin body.

## Observaciones técnicas importantes
1. Ruta detalle actual queda sin slash entre `users` e `id` por combinación de rutas:
   - Prefijo en proyecto: `path('api/v1/users', include('users.urls'))`
   - Ruta app: `path('<int:pk>/', ...)`

2. Si buscas URL convencional, sería:
   - Colección: `/api/v1/users/`
   - Detalle: `/api/v1/users/{id}/`

## Referencia de implementación
- Rutas app: `users/urls.py`
- Rutas proyecto: `core/urls.py`
- Vistas: `users/views.py`
- Serializer y validaciones: `users/serializers.py`
