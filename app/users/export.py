"""
CUSTOS User Export Utilities

CSV/Excel export functionality for users.
"""

import csv
import io
from typing import List, Optional
from datetime import datetime

from app.users.models import User


def export_users_to_csv(users: List[User]) -> str:
    """
    Export users to CSV format.
    
    Args:
        users: List of User objects to export
        
    Returns:
        CSV string content
    """
    output = io.StringIO()
    
    # Define CSV columns
    fieldnames = [
        'id',
        'email',
        'first_name',
        'last_name',
        'roles',
        'status',
        'is_active',
        'is_verified',
        'phone',
        'created_at',
        'last_login',
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write user data
    for user in users:
        writer.writerow({
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'roles': ','.join(user.roles) if user.roles else '',
            'status': user.status.value if hasattr(user, 'status') else '',
            'is_active': 'Yes' if user.is_active else 'No',
            'is_verified': 'Yes' if user.is_verified else 'No',
            'phone': user.phone or '',
            'created_at': user.created_at.isoformat() if user.created_at else '',
            'last_login': user.last_login.isoformat() if user.last_login else '',
        })
    
    return output.getvalue()


def generate_export_filename(format: str = "csv") -> str:
    """
    Generate timestamped filename for export.
    
    Args:
        format: File format (csv or excel)
        
    Returns:
        Filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"users_export_{timestamp}.{format}"
