from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Book(models.Model):
    name = models.CharField(max_length=50)
    author = models.CharField(max_length=20)
    url = models.CharField(max_length=50)
    brief = models.CharField(max_length=35)

    def __str__(self):
        return self.name


class DownUrl(models.Model):
    book_id = models.IntegerField()
    source = models.CharField(max_length=50)
    update_time = models.CharField(max_length=20)
    down_url = models.CharField(max_length=50)


    def __str__(self):
        return self.book_id