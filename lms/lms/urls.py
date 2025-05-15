from django.conf.urls import handler500, handler404
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path as url


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('librarian/', include('library.urls')),
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]
if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

# error handlers
handler500 = 'errorhandlers.views.e500'
handler404 = 'errorhandlers.views.e404handler'