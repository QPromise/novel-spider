from django.contrib import admin
from .models import Book,DownUrl

#admin管理Book以及DownUrl列表
class BookAdmin(admin.ModelAdmin):
    list_display = ['name','author','url','brief']

class DownUrlAdmin(admin.ModelAdmin):
    list_display = ['book_id','source','update_time','down_url']

admin.site.register(Book, BookAdmin)
admin.site.register(DownUrl,DownUrlAdmin)