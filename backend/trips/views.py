from rest_framework import viewsets, status, generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Profile, City, Trip, TripItinerary, JoinRequest, ChatMessage
from .serializers import (
    UserSerializer, ProfileSerializer, CitySerializer, TripSerializer,
    TripCreateSerializer, JoinRequestSerializer, ChatMessageSerializer,
    RegisterSerializer
)

class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    return Response(UserSerializer(request.user).data)

class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        city = self.get_object()
        trips = Trip.objects.filter(destination=city)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            
            # Debug logging
            print("Request FILES:", request.FILES)
            print("Request data:", request.data)
            
            # Validate file upload
            if 'photos' in request.FILES:
                photo = request.FILES['photos']
                
                # Validate file type
                valid_types = ['image/jpeg', 'image/png', 'image/jpg']
                if photo.content_type not in valid_types:
                    return Response(
                        {'photos': 'Invalid file type. Please upload JPG or PNG images only.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate file size (5MB limit)
                if photo.size > 5 * 1024 * 1024:
                    return Response(
                        {'photos': 'File too large. Maximum size is 5MB.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)
            
        except Exception as e:
            print("Profile update error:", str(e))
            return Response(
                {'error': 'An error occurred while updating profile. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.all().select_related('profile')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        user = self.get_object()
        trips = Trip.objects.filter(Q(host=user) | Q(members=user)).distinct()
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TripCreateSerializer
        return TripSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip = serializer.save()
        
        # Use the TripSerializer for the response to include all details
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    @permission_classes([IsAuthenticated])
    def join_request(self, request, pk=None):
        trip = self.get_object()
        user = request.user
        
        # Check if user is already a member
        if trip.host == user or trip.members.filter(id=user.id).exists():
            return Response(
                {"detail": "You are already a member of this trip."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's an existing request
        try:
            existing_request = JoinRequest.objects.get(trip=trip, user=user)
            if existing_request.status == 'pending':
                return Response(
                    {"detail": "You already have a pending request to join this trip."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing_request.status == 'rejected':
                # Update existing request to pending
                existing_request.status = 'pending'
                existing_request.save()
                return Response(
                    {"detail": "Join request sent successfully."}, 
                    status=status.HTTP_201_CREATED
                )
        except JoinRequest.DoesNotExist:
            # Create new join request
            JoinRequest.objects.create(trip=trip, user=user, status='pending')
            return Response(
                {"detail": "Join request sent successfully."}, 
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=True, methods=['get'])
    @permission_classes([IsAuthenticated])
    def join_status(self, request, pk=None):
        trip = self.get_object()
        user = request.user
        
        # Check if user is already a member
        if trip.host == user:
            return Response({"status": "host"})
        elif trip.members.filter(id=user.id).exists():
            return Response({"status": "member"})
        
        # Check for join request status
        try:
            join_request = JoinRequest.objects.get(trip=trip, user=user)
            return Response({"status": join_request.status})
        except JoinRequest.DoesNotExist:
            return Response({"status": "none"})

    @action(detail=True, methods=['get'])
    @permission_classes([IsAuthenticated])
    def pending_requests(self, request, pk=None):
        trip = self.get_object()
        if request.user != trip.host:
            return Response(
                {"detail": "Only the trip host can view pending requests."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_requests = JoinRequest.objects.filter(
            trip=trip,
            status='pending'
        ).select_related('user')
        
        serializer = JoinRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)

class TripRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JoinRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only trip hosts can see join requests for their trips
        return JoinRequest.objects.filter(
            trip__host=self.request.user,
            status='pending'
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None,request_pk=None):
        join_request = self.get_object()
        # Add user to trip members
        join_request.trip.members.add(join_request.user)
        join_request.status = 'accepted'
        join_request.save()
        
        return Response({"detail": "Join request approved."})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None,request_pk=None):
        join_request = self.get_object()
        join_request.status = 'rejected'
        join_request.save()
        
        return Response({"detail": "Join request rejected."})

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        trip_id = self.kwargs.get('trip_pk')
        trip = get_object_or_404(Trip, id=trip_id)
        
        # Make sure user is a member of the trip
        user = self.request.user
        if not (trip.host == user or trip.members.filter(id=user.id).exists()):
            return ChatMessage.objects.none()
        
        return ChatMessage.objects.filter(trip=trip).order_by('timestamp')
    
    def perform_create(self, serializer):
        trip_id = self.kwargs.get('trip_pk')
        trip = get_object_or_404(Trip, id=trip_id)
        
        # Make sure user is a member of the trip
        user = self.request.user
        if not (trip.host == user or trip.members.filter(id=user.id).exists()):
            raise permissions.PermissionDenied("You are not a member of this trip")
        
        serializer.save(trip=trip, user=user)

# Let's also implement a ManageRequestView to handle the frontend's request view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manage_requests(request):
    # Get all pending requests for trips where the user is the host
    join_requests = JoinRequest.objects.filter(
        trip__host=request.user,
        status='pending'
    ).select_related('trip', 'user')
    
    serializer = JoinRequestSerializer(join_requests, many=True)
    return Response(serializer.data)
