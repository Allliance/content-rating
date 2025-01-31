from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Just in case other fields were needed to be added
    
    class Meta:
        db_table = 'auth_user'