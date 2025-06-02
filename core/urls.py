from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import ( # Для эндпоинта /api/user/login
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.static import serve 
from django.conf import settings 
import os

urlpatterns = [
    path('', serve, {'document_root': os.path.join(settings.BASE_DIR, 'public'), 'path': 'index.html'}),
    path('admin/', admin.site.urls),
    path('api/', include('equipment.urls')),
    path('api/user/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]