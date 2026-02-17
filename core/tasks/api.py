# api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404
import json
import base64
from datetime import datetime
from .models import Task, TaskPriority, TaskStatus, TaskType, RecurrencePattern, TaskTemplate, TaskDependency, TaskTimeEntry, TaskComment, TaskActivity, TaskSharing, TaskAttachment
from core.models import User
from .forms import TaskForm
from tenants.models import Tenant as TenantModel


def validate_token(token):
    """
    Validate user token and return user object
    This is a simplified implementation - in production, use proper JWT or OAuth validation
    """
    # In a real implementation, this would validate the token against your authentication system
    try:
        # Assuming token is a user ID for this example
        user_id = int(token)
        user = User.objects.get(id=user_id)
        return user
    except (ValueError, User.DoesNotExist):
        return None


def parse_due_date(date_string):
    """
    Parse due date string to datetime object
    """
    if not date_string:
        return timezone.now()
    
    try:
        # Try different date formats
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'):
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        # If none of the formats work, return current time
        return timezone.now()
    except:
        return timezone.now()


@method_decorator(csrf_exempt, name='dispatch')
class MobileTaskCaptureView(View):
    """
    API endpoint for mobile task capture
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            # Validate user token
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            # Create task
            task = Task.objects.create(
                title=data.get('title', ''),
                task_description=data.get('description', ''),
                assigned_to=user,
                created_by=user,
                due_date=parse_due_date(data.get('due_date')),
                priority=data.get('priority', 'medium'),
                task_type=data.get('task_type', 'custom'),
                tenant_id=user.tenant_id
            )
            
            # Process image attachment if provided
            if data.get('image_data'):
                self.process_image_attachment(task, data['image_data'])
            
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'message': 'Task created successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def process_image_attachment(self, task, image_data):
        # Process base64 image data and save as attachment
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                header, image_data = image_data.split(',', 1)
                mime_type = header.split(':')[1].split(';')[0]
                filename = f"task_attachment_{task.id}.{mime_type.split('/')[1]}"
            else:
                mime_type = 'image/jpeg'
                filename = f"task_attachment_{task.id}.jpg"
            
            # Decode base64 image data
            image_binary = base64.b64decode(image_data)
            
            # Save as attachment
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            import os
            
            # Create a temporary file
            path = default_storage.save('temp_image.jpg', ContentFile(image_binary))
            temp_file_path = default_storage.path(path)
            
            # Create attachment record
            attachment = TaskAttachment.objects.create(
                task=task,
                # Note: We'd need to handle the file upload properly in a real implementation
                filename=filename,
                uploaded_by=task.created_by,
                file_size=len(image_binary),
                mime_type=mime_type,
                tenant_id=task.tenant_id
            )
            
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
        except Exception as e:
            print(f"Error processing image attachment: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class TaskListView(View):
    """
    API endpoint to list tasks for a user
    """
    def get(self, request):
        user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        user = validate_token(user_token)
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        # Get tasks for the user's tenant
        tasks = Task.objects.filter(tenant_id=user.tenant_id).select_related(
            'assigned_to', 'created_by', 'priority_ref', 'status_ref', 'task_type_ref'
        )
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.task_description,
                'assigned_to': task.assigned_to.email if task.assigned_to else None,
                'created_by': task.created_by.email if task.created_by else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'priority': task.priority,
                'status': task.status,
                'task_type': task.task_type,
                'is_overdue': task.is_overdue,
                'days_until_due': task.days_until_due
            })
        
        return JsonResponse({
            'success': True,
            'tasks': task_list
        })


@method_decorator(csrf_exempt, name='dispatch')
class TaskDetailView(View):
    """
    API endpoint to get a specific task
    """
    def get(self, request, task_id):
        user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        user = validate_token(user_token)
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        try:
            task = Task.objects.get(id=task_id, tenant_id=user.tenant_id)
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.task_description,
                    'assigned_to': task.assigned_to.email if task.assigned_to else None,
                    'created_by': task.created_by.email if task.created_by else None,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'priority': task.priority,
                    'status': task.status,
                    'task_type': task.task_type,
                    'is_overdue': task.is_overdue,
                    'days_until_due': task.days_until_due
                }
            })
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class TaskUpdateView(View):
    """
    API endpoint to update a task
    """
    def put(self, request, task_id):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            task = get_object_or_404(Task, id=task_id, tenant_id=user.tenant_id)
            
            # Update allowed fields
            if 'title' in data:
                task.title = data['title']
            if 'task_description' in data:
                task.task_description = data['task_description']
            if 'due_date' in data:
                task.due_date = parse_due_date(data['due_date'])
            if 'priority' in data:
                task.priority = data['priority']
            if 'status' in data:
                task.status = data['status']
            if 'task_type' in data:
                task.task_type = data['task_type']
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Task updated successfully',
                'task_id': task.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaskDeleteView(View):
    """
    API endpoint to delete a task
    """
    def delete(self, request, task_id):
        user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        user = validate_token(user_token)
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        try:
            task = Task.objects.get(id=task_id, tenant_id=user.tenant_id)
            task.delete()
            return JsonResponse({
                'success': True,
                'message': 'Task deleted successfully'
            })
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class TaskCompleteView(View):
    """
    API endpoint to mark a task as complete
    """
    def post(self, request, task_id):
        user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        user = validate_token(user_token)
        if not user:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        try:
            task = Task.objects.get(id=task_id, tenant_id=user.tenant_id)
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Task completed successfully'
            })
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class TaskCommentView(View):
    """
    API endpoint to add a comment to a task
    """
    def post(self, request, task_id):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            task = get_object_or_404(Task, id=task_id, tenant_id=user.tenant_id)
            
            comment = TaskComment.objects.create(
                task=task,
                author=user,
                content=data.get('content', ''),
                tenant_id=user.tenant_id
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Comment added successfully',
                'comment_id': comment.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaskAttachmentView(View):
    """
    API endpoint to upload an attachment to a task
    """
    def post(self, request, task_id):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            task = get_object_or_404(Task, id=task_id, tenant_id=user.tenant_id)
            
            # Get file data from the request
            file_data = data.get('file_data')
            filename = data.get('filename', 'attachment')
            mime_type = data.get('mime_type', 'application/octet-stream')
            
            if not file_data:
                return JsonResponse({'error': 'No file data provided'}, status=400)
            
            # Decode base64 file data
            file_binary = base64.b64decode(file_data)
            
            # Create attachment record
            attachment = TaskAttachment.objects.create(
                task=task,
                filename=filename,
                uploaded_by=user,
                file_size=len(file_binary),
                mime_type=mime_type,
                tenant_id=user.tenant_id
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Attachment uploaded successfully',
                'attachment_id': attachment.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaskTimeEntryView(View):
    """
    API endpoint to add a time entry to a task
    """
    def post(self, request, task_id):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            task = get_object_or_404(Task, id=task_id, tenant_id=user.tenant_id)
            
            time_entry = TaskTimeEntry.objects.create(
                task=task,
                user=user,
                date_logged=parse_due_date(data.get('date_logged', timezone.now().isoformat())),
                hours_spent=data.get('hours_spent', 0),
                description=data.get('description', ''),
                is_billable=data.get('is_billable', False),
                tenant_id=user.tenant_id
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Time entry added successfully',
                'time_entry_id': time_entry.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaskSharingView(View):
    """
    API endpoint to share a task with another user
    """
    def post(self, request, task_id):
        try:
            data = json.loads(request.body)
            user_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            
            user = validate_token(user_token)
            if not user:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            task = get_object_or_404(Task, id=task_id, tenant_id=user.tenant_id)
            
            # Get the user to share with
            shared_with_user_id = data.get('shared_with_user_id')
            if not shared_with_user_id:
                return JsonResponse({'error': 'User ID to share with is required'}, status=400)
            
            try:
                shared_with_user = User.objects.get(id=shared_with_user_id, tenant_id=user.tenant_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User to share with does not exist'}, status=404)
            
            # Create the sharing relationship
            sharing = TaskSharing.objects.create(
                task=task,
                shared_with_user=shared_with_user,
                shared_by=user,
                share_level=data.get('share_level', 'view'),
                expires_at=parse_due_date(data.get('expires_at')) if data.get('expires_at') else None,
                can_reassign=data.get('can_reassign', False),
                tenant_id=user.tenant_id
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Task shared with {shared_with_user.email}',
                'sharing_id': sharing.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)