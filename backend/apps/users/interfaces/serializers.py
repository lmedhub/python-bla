from rest_framework import serializers


class UserSerializer(serializers.Serializer[object]):
    """Reads a domain User. Only what other people may see: no is_active, no password data."""

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.CharField(read_only=True)


class LoginSerializer(serializers.Serializer[object]):
    email = serializers.EmailField()
    # Passwords are compared exactly: never trim them.
    password = serializers.CharField(trim_whitespace=False, write_only=True)


class SessionSerializer(serializers.Serializer[object]):
    """Login and refresh answer with the same shape, so the frontend restores state one way."""

    access = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)
