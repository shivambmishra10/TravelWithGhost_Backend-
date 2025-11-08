from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'cities', views.CityViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'trips', views.TripViewSet)
router.register(r'trip-requests', views.TripRequestViewSet, basename='trip-requests')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.CustomObtainAuthToken.as_view(), name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/user/', views.get_user, name='user'),
    path('profile/', views.ProfileViewSet.as_view({'get': 'list', 'post': 'create'}), name='profile'),
    path('create-trip/', views.TripViewSet.as_view({'post': 'create'}), name='create-trip'),
    # Add explicit URLs for join-request and join-status
    path('trips/<int:pk>/join-request/', views.TripViewSet.as_view({'post': 'join_request'}), name='join-request'),
    path('trips/<int:pk>/join-status/', views.TripViewSet.as_view({'get': 'join_status'}), name='join-status'),
    path('trips/<int:pk>/pending-requests/', views.TripViewSet.as_view({'get': 'pending_requests'}), name='pending-requests'),
    path('trips/<int:trip_pk>/chat/', views.ChatMessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='chat')
]

urlpatterns += [
    path('trip-requests/', views.manage_requests, name='manage-requests'),
]