from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404
from app.views import custom_404_view, custom_500_view
from django.conf import settings
from django.conf.urls.static import static


handler500 = custom_500_view
handler404 = custom_404_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include('app.urls')),
]

if settings.DEBUG is False:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)