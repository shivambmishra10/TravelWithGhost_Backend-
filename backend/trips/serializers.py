from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile, City, Trip, TripItinerary, JoinRequest, ChatMessage

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(read_only=True)
    
    def get_profile(self, obj):
        try:
            profile = Profile.objects.get(user=obj)
            request = self.context.get('request')
            photos_url = None
            if profile.photos:
                if request is not None:
                    photos_url = request.build_absolute_uri(profile.photos.url)
                else:
                    photos_url = profile.photos.url
            
            # Get the display name - use name if set, otherwise format email nicely
            display_name = profile.name if profile.name else self.format_email_to_name(obj.email)
            
            return {
                'name': display_name,
                'current_location': profile.current_location or "Location not set",
                'age': profile.age or None,
                'gender': profile.gender or None,
                'profession': profile.profession or "Adventurer",
                'photos': photos_url,
                'is_profile_complete': bool(profile.name and profile.current_location and profile.age and profile.gender)
            }
        except Profile.DoesNotExist:
            # Provide default values for users without profiles
            return {
                'name': self.format_email_to_name(obj.email),
                'current_location': "Location not set",
                'age': None,
                'gender': None,
                'profession': "Adventurer",
                'photos': None,
                'is_profile_complete': False
            }
    
    def format_email_to_name(self, email):
        """Convert email to a presentable name."""
        if not email:
            return "Anonymous Traveler"
        # Remove @domain.com and capitalize each word
        name = email.split('@')[0]
        # Replace dots and underscores with spaces
        name = name.replace('.', ' ').replace('_', ' ')
        # Capitalize each word
        return ' '.join(word.capitalize() for word in name.split())
            
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'date_joined']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'name', 'current_location', 'age', 'gender', 'profession', 'photos']

class CitySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
        
    class Meta:
        model = City
        fields = ['id', 'name', 'image']

class TripItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripItinerary
        fields = ['day', 'description']

class TripSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    destination = CitySerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source='destination',
        write_only=True
    )
    members = UserSerializer(many=True, read_only=True)
    itinerary_items = TripItinerarySerializer(many=True, read_only=True)
    current_members_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'host', 'group_name', 'destination', 'destination_id',
            'start_date', 'end_date', 'description', 'budget', 'min_age', 'max_age',
            'required_members', 'members', 'itinerary_items', 'current_members_count',
            'created_at'
        ]

class TripCreateSerializer(serializers.ModelSerializer):
    itinerary = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = Trip
        fields = [
            'id', 'group_name', 'destination', 'start_date', 'end_date',
            'description', 'budget', 'min_age', 'max_age', 'required_members', 'itinerary'
        ]
    
    def create(self, validated_data):
        itinerary_data = validated_data.pop('itinerary')
        validated_data['host'] = self.context['request'].user
        trip = Trip.objects.create(**validated_data)
        
        for item in itinerary_data:
            TripItinerary.objects.create(
                trip=trip,
                day=item['day'],
                description=item['description']
            )
        
        return trip

class JoinRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    trip = TripSerializer(read_only=True)
    
    class Meta:
        model = JoinRequest
        fields = ['id', 'trip', 'user', 'status', 'created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'message', 'timestamp']

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1']
        )
        
        # Create empty profile
        Profile.objects.create(
            user=user,
            name="",
            current_location="",
            age=0,
            gender=""
        )
        
        return user
