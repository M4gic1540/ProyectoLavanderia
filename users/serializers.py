from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    # Forzamos a que el email sea obligatorio y único
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}, # No mostrar la contraseña en respuestas GET
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate_email(self, value):
        """Validación personalizada para que el email sea único."""
        # Al actualizar, excluimos al propio usuario de la búsqueda
        user_id = self.context.get('user_id')
        queryset = User.objects.filter(email=value)
        if user_id:
            queryset = queryset.exclude(id=user_id)
            
        if queryset.exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value

    def create(self, validated_data):
        """Crea el usuario encriptando la contraseña."""
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Actualiza el usuario manejando correctamente el password si cambia."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance