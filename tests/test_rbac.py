"""
CUSTOS RBAC Tests
"""

import pytest
from app.auth.rbac import (
    SystemRole, Permission, ROLE_PERMISSIONS,
    check_permission, check_any_permission, check_all_permissions,
    get_role_level, can_manage_role, get_default_permissions,
)


class TestRBAC:
    """Test role-based access control."""
    
    def test_system_roles_defined(self):
        """Test all system roles are defined."""
        assert SystemRole.SUPER_ADMIN.value == "super_admin"
        assert SystemRole.PRINCIPAL.value == "principal"
        assert SystemRole.TEACHER.value == "teacher"
        assert SystemRole.STUDENT.value == "student"
        assert SystemRole.PARENT.value == "parent"
    
    def test_super_admin_has_all_permissions(self):
        """Test super admin has all permissions."""
        super_admin_perms = ROLE_PERMISSIONS[SystemRole.SUPER_ADMIN]
        assert super_admin_perms == set(Permission)
    
    def test_teacher_permissions(self):
        """Test teacher has correct permissions."""
        teacher_perms = ROLE_PERMISSIONS[SystemRole.TEACHER]
        
        # Should have
        assert Permission.LESSON_CREATE in teacher_perms
        assert Permission.QUESTION_CREATE in teacher_perms
        assert Permission.ASSIGNMENT_GRADE in teacher_perms
        
        # Should not have
        assert Permission.USER_DELETE not in teacher_perms
        assert Permission.TENANT_MANAGE not in teacher_perms
    
    def test_student_permissions(self):
        """Test student has limited permissions."""
        student_perms = ROLE_PERMISSIONS[SystemRole.STUDENT]
        
        # Should have
        assert Permission.LESSON_VIEW in student_perms
        assert Permission.ASSIGNMENT_SUBMIT in student_perms
        assert Permission.AI_DOUBT_SOLVER in student_perms
        
        # Should not have
        assert Permission.LESSON_CREATE not in student_perms
        assert Permission.ASSIGNMENT_GRADE not in student_perms
    
    def test_check_permission(self):
        """Test permission checking."""
        user_perms = {"lesson:view", "lesson:create", "question:view"}
        
        assert check_permission(user_perms, Permission.LESSON_VIEW)
        assert check_permission(user_perms, Permission.LESSON_CREATE)
        assert not check_permission(user_perms, Permission.LESSON_DELETE)
    
    def test_check_any_permission(self):
        """Test any permission checking."""
        user_perms = {"lesson:view"}
        
        assert check_any_permission(
            user_perms, 
            [Permission.LESSON_VIEW, Permission.LESSON_CREATE]
        )
        assert not check_any_permission(
            user_perms, 
            [Permission.LESSON_DELETE, Permission.LESSON_CREATE]
        )
    
    def test_check_all_permissions(self):
        """Test all permissions checking."""
        user_perms = {"lesson:view", "lesson:create"}
        
        assert check_all_permissions(
            user_perms, 
            [Permission.LESSON_VIEW, Permission.LESSON_CREATE]
        )
        assert not check_all_permissions(
            user_perms, 
            [Permission.LESSON_VIEW, Permission.LESSON_DELETE]
        )
    
    def test_role_hierarchy(self):
        """Test role hierarchy levels."""
        assert get_role_level("super_admin") > get_role_level("principal")
        assert get_role_level("principal") > get_role_level("teacher")
        assert get_role_level("teacher") > get_role_level("student")
    
    def test_can_manage_role(self):
        """Test role management permissions."""
        # Super admin can manage all
        assert can_manage_role(["super_admin"], "principal")
        assert can_manage_role(["super_admin"], "teacher")
        
        # Principal can manage teachers
        assert can_manage_role(["principal"], "teacher")
        assert can_manage_role(["principal"], "student")
        
        # Principal cannot manage super admin
        assert not can_manage_role(["principal"], "super_admin")
        
        # Teacher cannot manage other teachers
        assert not can_manage_role(["teacher"], "teacher")
    
    def test_get_default_permissions(self):
        """Test getting default permissions for role."""
        teacher_perms = get_default_permissions("teacher")
        
        assert "lesson:view" in teacher_perms
        assert "lesson:create" in teacher_perms
        assert len(teacher_perms) > 0
        
        # Invalid role
        invalid_perms = get_default_permissions("invalid_role")
        assert len(invalid_perms) == 0
