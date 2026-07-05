from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404  # <-- Línea corregida aquí
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from drf_spectacular.utils import extend_schema

# --- VISTAS PARA LA COLECCIÓN (LISTAR Y CREAR) ---

@extend_schema(responses=UserSerializer(many=True))
@api_view(['GET', 'POST'])
def user_collection(request):
    """
    GET: Listar todos los usuarios.
    POST: Crear un nuevo usuario con validaciones.
    """
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Buenas prácticas: Retorna errores estructurados 400 Bad Request
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- VISTAS PARA UN ELEMENTO INDIVIDUAL (OBTENER, ACTUALIZAR, ELIMINAR) ---

@extend_schema(responses=UserSerializer)
@api_view(['GET', 'PUT', 'DELETE'])
def user_element(request, pk):
    """
    GET: Obtener detalles de un usuario por ID.
    PUT: Actualizar campos de un usuario por ID.
    DELETE: Eliminar un usuario por ID.
    """
    # Gestión de errores: Si el ID no existe, responde automáticamente un 404 estructurado
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {"error": f"Usuario con ID {pk} no encontrado."}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Pasamos el contexto del ID para la validación del email único
        serializer = UserSerializer(user, data=request.data, context={'user_id': pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            user.delete()
            return Response(
                {"message": f"Usuario con ID {pk} eliminado correctamente."}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": "No se pudo eliminar el usuario debido a un error del servidor."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )