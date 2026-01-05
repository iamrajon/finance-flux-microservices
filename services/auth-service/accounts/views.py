from rest_framework import generics 
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.jwt_serializers import CustomTokenObtainPairSerializer
from accounts.events import publish_event
from accounts.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    TokenRefreshSerializer
)

User = get_user_model()


class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({
            'service': 'User Service',
            'status': 'healthy'
        })


class RegisterUserAPIView(generics.CreateAPIView):
    """User Registration view function"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Publish user registration event
        publish_event('user.registered', {
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username
        })

        # generate jwt tokens with custom claims
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        response_data = {
            "success": True,
            "message": "User Registered Successfully",
            "user": UserProfileSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    

class LoginUserAPIView(generics.GenericAPIView):
    """User Login view function"""
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Authenticate User
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(email=user_obj.email, password=password)
        except User.DoesNotExist:
            user = None 

        if user is not None:
            refresh = CustomTokenObtainPairSerializer.get_token(user)

            response_data = {
                "success": True,
                "message": "Login Successful!",
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "error": "Invalid Credentials"
        }, status=status.HTTP_401_UNAUTHORIZED)
    

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return UserUpdateSerializer
        return UserProfileSerializer
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        # Publish user update event
        publish_event('user.updated', {
            'user_id': request.user.id,
            'email': request.user.email
        })
        
        return response
    

class RefreshTokenAPIView(generics.GenericAPIView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data['refresh']

        try:
            refresh = RefreshToken(refresh_token)
            return Response({'success': True, 'access': str(refresh.access_token)})
        except Exception:
            return Response({'success': False, 'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'success': False, 'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
            return Response({'success': True, 'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'success': False, 'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

    

