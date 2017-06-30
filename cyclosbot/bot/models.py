from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TelegramUser(models.Model):
    registered = models.BooleanField(default=False)
    chat_id = models.AutoField(primary_key=True)
    django_user = models.ForeignKey(User, on_delete=models.PROTECT)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20) # i don't like this way to store the password but i has to do it
    conversation_status = models.PositiveIntegerField(default=0)
