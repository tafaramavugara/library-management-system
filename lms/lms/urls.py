from django.conf.urls import handler500, handler404
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('librarian/', include('library.urls'))
]


# error handlers
handler500 = 'errorhandlers.views.e500'
handler404 = 'errorhandlers.views.e404handler'