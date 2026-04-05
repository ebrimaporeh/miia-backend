from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, logout
from django.test import RequestFactory
from django_rest_passwordreset.views import ResetPasswordRequestToken
from django_rest_passwordreset.serializers import EmailSerializer
from apps.applications.models import Application
from apps.accounts.email_utils import send_verification_email, verify_email_token


from apps.accounts.serializers.auth_serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    TeacherProfileSerializer,
    StudentProfileSerializer,
    ParentProfileSerializer,
    StaffProfileSerializer
)

User = get_user_model()

class LoginView(TokenObtainPairView):
    """User login with JWT"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterView(generics.CreateAPIView):
    """User registration"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        try:
            send_verification_email(user, request)
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")
        
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User created successfully. Please check your email to verify your account.'
        }
        
        # Get application if exists
        if user.role == 'applicant':
            from apps.applications.models import Application
            try:
                application = Application.objects.get(applicant=user)
                response_data['application'] = {
                    'id': str(application.id),
                    'status': application.status,
                    'current_step': application.current_step
                }
            except Application.DoesNotExist:
                pass
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    

class LogoutView(APIView):
    """User logout - simple logout without token blacklisting"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Clear the session on server side
            logout(request)
            return Response(
                {'message': 'Successfully logged out'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ChangePasswordView(generics.GenericAPIView):
    """Change user password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Wrong password'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, 
                      status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveAPIView):
    """Get user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Return appropriate profile based on user type
        if user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            serializer = TeacherProfileSerializer(user.teacher_profile)
        elif user.role == 'student' and hasattr(user, 'student_profile'):
            serializer = StudentProfileSerializer(user.student_profile)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            serializer = ParentProfileSerializer(user.parent_profile)
        elif user.role == 'staff' and hasattr(user, 'staff_profile'):
            serializer = StaffProfileSerializer(user.staff_profile)
        else:
            serializer = self.get_serializer(user)
        
        return Response(serializer.data)

class UpdateProfileView(generics.UpdateAPIView):
    """Update user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user

class ForgotPasswordView(generics.GenericAPIView):
    """Request password reset email"""
    permission_classes = [AllowAny]
    serializer_class = EmailSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use django-rest-passwordreset's built-in view
        reset_view = ResetPasswordRequestToken.as_view()
        
        factory = RequestFactory()
        new_request = factory.post('/api/auth/forgot-password/', 
                                  data={'email': serializer.validated_data['email']})
        
        response = reset_view(new_request)
        return Response({'message': 'Password reset email sent if email exists'})

class CheckAuthView(generics.GenericAPIView):
    """Check if user is authenticated"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': request.user.role,
            }
        })

class VerifyEmailView(APIView):
    """Verify user email using token"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        token = request.query_params.get('token')
        
        if not token:
            return Response(
                {'error': 'Verification token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = verify_email_token(token)
        
        if not user_id:
            return Response(
                {'error': 'Invalid or expired verification token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_email_verified:
            return Response(
                {'message': 'Email already verified'},
                status=status.HTTP_200_OK
            )
        
        # Verify the user
        user.is_email_verified = True
        user.is_active = True  # Activate user after email verification
        user.email_verification_token = None
        user.save()
        
        return Response(
            {'message': 'Email verified successfully. You can now log in.'},
            status=status.HTTP_200_OK
        )


class ResendVerificationEmailView(APIView):
    """Resend verification email"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist for security
            return Response(
                {'message': 'If an account exists, a verification email will be sent'},
                status=status.HTTP_200_OK
            )
        
        if user.is_email_verified:
            return Response(
                {'message': 'Email already verified'},
                status=status.HTTP_200_OK
            )
        
        # Send new verification email
        send_verification_email(user, request)
        
        return Response(
            {'message': 'Verification email sent. Please check your inbox.'},
            status=status.HTTP_200_OK
        )
