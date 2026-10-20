from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

def healthz(request):
    """Lightweight liveness endpoint; database checks are performed separately."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('library.urls')),
]