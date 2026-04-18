from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.accounts.models import Teacher, Student, Parent, Staff
from django.contrib.auth.models import Permission

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile - ONLY basic user info"""
    name = serializers.SerializerMethodField()
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'first_name', 'last_name', 
            'role', 'phone', 'avatar', 'address','date_joined', 'permissions',
             
        ]
        read_only_fields = ('id', 'email', 'role', 'date_joined')
    
    def get_name(self, obj):
        return obj.get_full_name() or obj.email
    
    def get_status(self, obj):
        return 'active' if obj.is_active else 'inactive'
    
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_permissions(self, obj):
        # Keep this method as is
        if not obj.is_authenticated:
            return []
        
        perms = set()
        for group in obj.groups.all():
            for perm in group.permissions.all():
                perms.add(perm.codename)
        
        if obj.role == 'admin':
            all_perms = Permission.objects.values_list('codename', flat=True)
            perms.update(all_perms)
        
        return list(perms)

class RoleProfileSerializer(serializers.Serializer):
    """Serializer to get role-specific profile"""
    
    def to_representation(self, instance):
        """Get profile data for the user"""
        user = instance
        
        if user.role == 'parent' and hasattr(user, 'parent_profile'):
            return ParentProfileSerializer(user.parent_profile).data
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            return TeacherProfileSerializer(user.teacher_profile).data
        elif user.role == 'student' and hasattr(user, 'student_profile'):
            return StudentProfileSerializer(user.student_profile).data
        elif user.role == 'staff' and hasattr(user, 'staff_profile'):
            return StaffProfileSerializer(user.staff_profile).data
        
        return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that returns minimal token + rich user response"""
    
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        #  Keep JWT minimal (only identity + auth metadata)
        token["role"] = user.role
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        #  Always include full user profile in response body
        data["user"] = UserProfileSerializer(
            user,
            context=self.context
        ).data

        #  Attach role-based profile (response only, NOT token)
        data["profile"] = self.get_role_profile(user)

        return data

    def get_role_profile(self, user):
        """Return role-specific profile data safely"""

        if user.role == "student" and hasattr(user, "student_profile"):
            return {
                "student_id": user.student_profile.student_id,
                "gender": user.student_profile.gender,
                "status": user.student_profile.status,
                "performance": user.student_profile.performance,
                "guardian_name": user.student_profile.guardian_name,
                "guardian_phone": user.student_profile.guardian_phone,
                "guardian_email": user.student_profile.guardian_email,
            }

        if user.role == "parent" and hasattr(user, "parent_profile"):
            return {
                "relationship": user.parent_profile.relationship,
                "occupation": user.parent_profile.occupation,
                "phone": user.parent_profile.phone,
                "alternate_phone": user.parent_profile.alternate_phone,
                "address": user.parent_profile.address,
                "children_count": user.parent_profile.children.count(),
            }

        if user.role == "teacher" and hasattr(user, "teacher_profile"):
            return {
                "employee_id": user.teacher_profile.employee_id,
                "qualification": user.teacher_profile.qualification,
                "specialization": user.teacher_profile.specialization,
                "department": user.teacher_profile.department,
                "position": user.teacher_profile.position,
            }

        if user.role == "staff" and hasattr(user, "staff_profile"):
            return {
                "staff_id": user.staff_profile.staff_id,
                "department": user.staff_profile.department,
                "position": user.staff_profile.position,
            }

        return None

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'avatar', 'address')
    
    def validate_email(self, value):
        """Validate email uniqueness if changed"""
        if self.instance and self.instance.email != value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'first_name', 'last_name', 
                 'role', 'phone')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate role
        valid_types = ['admin', 'teacher', 'student', 'parent', 'staff', 'applicant']
        if attrs['role'] not in valid_types:
            raise serializers.ValidationError({"role": f"Must be one of: {', '.join(valid_types)}"})
        
        # Additional validation for admin creation
        if attrs['role'] == 'admin':
            request = self.context.get('request')
            if not request or not request.user.is_authenticated or not request.user.is_superuser:
                raise serializers.ValidationError({"role": "Only superusers can create admin accounts."})
        
        return attrs
    
    def create(self, validated_data):
        # Remove confirm_password from data
        validated_data.pop('confirm_password')
        
        # Create username from email (first part before @)
        username = validated_data['email'].split('@')[0]
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Set is_active based on role (admin and staff might need approval)
        is_active = validated_data['role'] not in ['staff']  # Staff need approval
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            phone=validated_data.get('phone', ''),
            is_active=is_active
        )
        
        return user

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for admin profile"""

    name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'role',
            'phone',
            'avatar',
            'address',
            'date_joined',
            'permissions',
        ]

    def get_name(self, obj):
        return obj.get_full_name() or obj.email

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None

    def get_permissions(self, obj):
        if not obj.is_authenticated:
            return []

        perms = set()

        for group in obj.groups.all():
            for perm in group.permissions.all():
                perms.add(perm.codename)

        if obj.role == "admin":
            from django.contrib.auth.models import Permission
            all_perms = Permission.objects.values_list('codename', flat=True)
            perms.update(all_perms)

        return list(perms)


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for teacher profile"""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Teacher
        fields = ('user', 'employee_id', 
                 'qualification', 'specialization', 'joining_date', 'department', 'position')

class ChildStudentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ('student_id', 'user')

class ParentProfileSerializer(serializers.ModelSerializer):
    """Serializer for parent profile"""

    children = ChildStudentSerializer(many=True, read_only=True)
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Parent
        fields = (
            'user',
            'occupation',
            'relationship',
            'children',
        )

class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for student profile"""

    user = UserProfileSerializer(read_only=True)
    parent = ParentProfileSerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = ('user', 'student_id', 
                 'enrollment_date', 'guardian_name', 'guardian_phone', 'guardian_email', 'date_of_birth', 'gender', 'parent')

class StaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for staff profile"""

    
   
    class Meta:
        model = Staff
        fields = ( 'staff_id', 
                 'department', 'position', 'joining_date')