from django.core.exceptions import ValidationError

def user_directory_path(instance, filename):
  return 'user_{0}/{1}'.format(instance.user.id, filename)

def file_size(value):
    limit = 5 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 5 MiB.')