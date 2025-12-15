# Building TravelWithGhost: Django Backend Architecture

## Part 2: Backend Deep Dive - Models, API, and Business Logic

*Understanding the heart of the application*

---

## Introduction

In Part 1, we covered the overall system architecture. Now, let's dive deep into the Django backend - the brain of TravelWithGhost. We'll explore the data models, API design, authentication, and key architectural decisions.

---

## Database Schema & Models

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│    User     │────────>│   Profile   │
│  (Django)   │ 1     1 │             │
└─────────────┘         └─────────────┘
      │                       
      │ 1                     
      │                       
      │ N                     
      ▼                       
┌─────────────┐         ┌─────────────┐
│    Trip     │────────>│    City     │
│             │ N     1 │             │
└─────────────┘         └─────────────┘
      │                       
      │ 1                     
      │                       
      │ N                     
      ▼                       
┌─────────────┐               
│ TripItinerary│               
│             │               
└─────────────┘               
      
┌─────────────┐         ┌─────────────┐
│    User     │<───────>│    Trip     │
│             │ N     N │  (members)  │
└─────────────┘         └─────────────┘
      │                       │
      │                       │
      └───────┐       ┌───────┘
              ▼       ▼
        ┌─────────────────┐
        │  JoinRequest    │
        │                 │
        └─────────────────┘

┌─────────────┐         ┌─────────────┐
│    User     │────────>│ ChatMessage │
│             │ 1     N │             │
└─────────────┘         └─────────────┘
      │                       │
      │                       │ N
      │                       ▼
      │                 ┌─────────────┐
      └────────────────>│    Trip     │
                      N └─────────────┘
```

### Core Models Explained

#### 1. **Profile Model**
```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    current_location = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    profession = models.CharField(max_length=100, blank=True, null=True)
    photos = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
```

**Design Decisions**:
- **Separate from User**: Keeps auth separate from profile data
- **OneToOne Relationship**: Each user has exactly one profile
- **Nullable Profession**: Optional field for flexibility
- **ImageField**: Django handles file uploads

**Why not extend User model directly?**
- Cleaner separation of concerns
- Easier to modify profile fields
- Better for future multi-tenancy

#### 2. **City Model**
```python
class City(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='')
```

**Design Decisions**:
- Simple model for destinations
- Image stored at root of media folder
- Future: Add description, country, coordinates

**Room for Improvement**:
- Add more metadata (country, timezone, description)
- Add coordinates for map integration
- Add popularity score

#### 3. **Trip Model**
```python
class Trip(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_trips')
    group_name = models.CharField(max_length=100)
    destination = models.ForeignKey(City, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    min_age = models.IntegerField()
    max_age = models.IntegerField()
    required_members = models.IntegerField()
    members = models.ManyToManyField(User, related_name='joined_trips')
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Features**:
- **Host**: The trip creator
- **Members**: ManyToMany for multiple travelers
- **Age Restrictions**: Business logic for age-appropriate trips
- **Timestamps**: Track when trip was created

**Related Names**:
- `hosted_trips`: Access all trips a user hosts
- `joined_trips`: Access all trips a user joined

**Why separate host from members?**
- Clear ownership
- Different permissions
- Host can't "leave" the trip

#### 4. **TripItinerary Model**
```python
class TripItinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itinerary_items')
    day = models.IntegerField()
    description = models.TextField()
```

**Design Pattern**: Separate model for itinerary
- Each day is a separate record
- Easy to add/remove days
- Flexible for complex itineraries

**Room for Improvement**:
- Add time of day
- Add location per day
- Add costs

#### 5. **JoinRequest Model**
```python
class JoinRequest(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('trip', 'user')
```

**Key Features**:
- **Status Choices**: Explicit states
- **Unique Together**: Prevent duplicate requests
- **Cascading Delete**: If trip deleted, requests go too

**Workflow**:
1. User requests to join
2. Host sees pending requests
3. Host accepts/rejects
4. If accepted, user added to trip members

#### 6. **ChatMessage Model**
```python
class ChatMessage(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Simple Design**:
- Basic chat functionality
- Ordered by timestamp
- Tied to specific trip

**Future Enhancements**:
- Read receipts
- Attachments
- Reactions/emojis
- WebSocket for real-time

---

## API Architecture

### RESTful Endpoint Design

```
Authentication
├── POST   /api/register/           # User registration
├── POST   /api/login/              # Get auth token
└── POST   /api/logout/             # Invalidate token

Profile Management
├── GET    /api/profile/            # Get user profile
└── PUT    /api/profile/            # Update profile

Destinations
└── GET    /api/cities/             # List all cities

Trips
├── GET    /api/trips/              # List all trips
├── POST   /api/trips/              # Create new trip
├── GET    /api/trips/{id}/         # Trip details
├── PUT    /api/trips/{id}/         # Update trip
├── DELETE /api/trips/{id}/         # Delete trip
├── POST   /api/trips/{id}/join/    # Join request
├── GET    /api/trips/{id}/members/ # List members
└── GET    /api/trips/{id}/chat/    # Get chat messages

Join Requests
├── GET    /api/join-requests/       # User's requests
├── GET    /api/manage-requests/     # Host's requests
└── PATCH  /api/join-requests/{id}/  # Accept/reject

Users
└── GET    /api/users/{id}/          # Public profile
```

### Serializers Deep Dive

#### User Serializer with Profile
```python
class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    def get_profile(self, obj):
        try:
            profile = Profile.objects.get(user=obj)
            # Build absolute URL for photos
            request = self.context.get('request')
            photos_url = None
            if profile.photos:
                if request is not None:
                    photos_url = request.build_absolute_uri(profile.photos.url)
                else:
                    photos_url = profile.photos.url
            
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
            return {
                'name': self.format_email_to_name(obj.email),
                'current_location': "Location not set",
                'age': None,
                'gender': None,
                'profession': "Adventurer",
                'photos': None,
                'is_profile_complete': False
            }
```

**Smart Features**:
1. **Graceful Defaults**: Works even without profile
2. **Absolute URLs**: Frontend gets complete image URLs
3. **Email Formatting**: Converts email to name if needed
4. **Profile Completeness**: Boolean for UI hints

#### Nested Trip Serializer
```python
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
```

**Why This Pattern?**
- **Read**: Nested data for display
- **Write**: Simple ID for creation
- **Performance**: Avoids N+1 queries

---

## Authentication System

### Token-Based Auth Flow

```
1. User Registration
   POST /api/register/
   { "username", "email", "password1", "password2" }
   ↓
   Creates User + Profile
   ↓
   Returns success

2. Login
   POST /api/login/
   { "username", "password" }
   ↓
   Validates credentials
   ↓
   Returns token
   
3. Authenticated Requests
   GET /api/trips/
   Headers: { Authorization: "Token abc123..." }
   ↓
   Validates token
   ↓
   Returns data
```

### Authentication Implementation

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_trip(request):
    serializer = TripCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
```

**Key Points**:
- Token stored in database
- Token sent in `Authorization` header
- Django middleware validates automatically

---

## Business Logic Examples

### 1. **Trip Creation with Itinerary**

```python
class TripCreateSerializer(serializers.ModelSerializer):
    itinerary = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
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
```

**Why This Approach?**
- Single API call creates trip + itinerary
- Atomic operation (all or nothing)
- Clean separation of concerns

### 2. **Join Request Workflow**

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    
    # Check if user is already a member
    if request.user in trip.members.all():
        return Response({'error': 'Already a member'}, status=400)
    
    # Check if user is the host
    if trip.host == request.user:
        return Response({'error': 'Host cannot join own trip'}, status=400)
    
    # Check age restrictions
    profile = request.user.profile
    if profile.age < trip.min_age or profile.age > trip.max_age:
        return Response({'error': 'Age restriction'}, status=400)
    
    # Create join request
    join_request, created = JoinRequest.objects.get_or_create(
        trip=trip,
        user=request.user,
        defaults={'status': 'pending'}
    )
    
    if not created:
        return Response({'error': 'Request already exists'}, status=400)
    
    return Response({'message': 'Join request sent'}, status=201)
```

**Validation Steps**:
1. Trip exists?
2. Already a member?
3. User is host?
4. Age restrictions met?
5. Previous request exists?

### 3. **Profile Completion Check**

```python
def get_profile(self, obj):
    # ... profile data ...
    return {
        # ... other fields ...
        'is_profile_complete': bool(
            profile.name and 
            profile.current_location and 
            profile.age and 
            profile.gender
        )
    }
```

**Use Case**: Frontend shows profile completion banner

---

## Common Patterns & Best Practices

### 1. **DRY with SerializerMethodField**
```python
photos_url = request.build_absolute_uri(profile.photos.url)
```
- Reusable across serializers
- Consistent URL format
- Works in any context

### 2. **Graceful Error Handling**
```python
try:
    profile = Profile.objects.get(user=obj)
except Profile.DoesNotExist:
    return default_profile_data
```
- Never crashes on missing data
- Provides sensible defaults
- Better UX

### 3. **Related Names for Clarity**
```python
host = models.ForeignKey(User, related_name='hosted_trips')
members = models.ManyToManyField(User, related_name='joined_trips')
```
- `user.hosted_trips.all()` - clear intent
- `user.joined_trips.all()` - easy queries

### 4. **Custom Methods in Models**
```python
class Trip(models.Model):
    def current_members_count(self):
        return self.members.count() + 1  # +1 for host
```
- Reusable logic
- Consistent calculations
- Easy to test

---

## Database Optimization Techniques

### 1. **Select Related (Foreign Keys)**
```python
trips = Trip.objects.select_related('host', 'destination').all()
```
- Reduces queries from N+1 to 2
- Use for ForeignKey relationships

### 2. **Prefetch Related (Many-to-Many)**
```python
trips = Trip.objects.prefetch_related('members', 'itinerary_items').all()
```
- Optimizes ManyToMany queries
- Separate queries, but fewer overall

### 3. **Indexing**
```python
class Meta:
    indexes = [
        models.Index(fields=['created_at']),
        models.Index(fields=['start_date']),
    ]
```
- Faster queries on frequent filters
- Trade-off: slightly slower writes

---

## Testing Strategy

### Unit Tests
```python
class TripModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test')
        self.city = City.objects.create(name='Test City')
        
    def test_trip_creation(self):
        trip = Trip.objects.create(
            host=self.user,
            destination=self.city,
            # ... other fields ...
        )
        self.assertEqual(trip.host, self.user)
        self.assertEqual(trip.current_members_count(), 1)
```

### API Tests
```python
class TripAPITest(APITestCase):
    def test_create_trip_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post('/api/trips/', data)
        self.assertEqual(response.status_code, 201)
```

---

## Challenges & Solutions

### Challenge 1: Image URL Generation
**Problem**: Frontend needs full URLs, not relative paths

**Solution**: `request.build_absolute_uri()`
```python
photos_url = request.build_absolute_uri(profile.photos.url)
# Returns: https://api.travelwithghost.com/media/profile_photos/user1.jpg
```

### Challenge 2: Profile Creation Timing
**Problem**: User created before profile

**Solution**: Signal or explicit profile creation in registration

### Challenge 3: Join Request Duplicates
**Problem**: Users could spam join requests

**Solution**: `unique_together` constraint + `get_or_create()`

---

## Environment Configuration

### settings.py Structure
```python
# Database
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL')
    )
}

# Media files
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS').split(',')

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')
```

**Why This Pattern?**
- All secrets in `.env`
- Easy to change per environment
- No hardcoded values

---

## API Documentation Example

### Endpoint: Create Trip
```
POST /api/trips/

Headers:
  Authorization: Token abc123...
  Content-Type: application/json

Body:
{
  "group_name": "Goa Beach Party",
  "destination_id": 1,
  "start_date": "2025-12-01",
  "end_date": "2025-12-05",
  "description": "Beach, parties, and relaxation",
  "min_age": 21,
  "max_age": 35,
  "required_members": 6,
  "itinerary": [
    {"day": 1, "description": "Arrive and beach"},
    {"day": 2, "description": "Water sports"},
    {"day": 3, "description": "Party night"}
  ]
}

Response: 201 Created
{
  "id": 5,
  "group_name": "Goa Beach Party",
  ...
}
```

---

## What's Next?

In **Part 3**, we'll explore the Next.js frontend:
- Component structure
- State management
- API integration patterns
- Form handling

---

## Key Takeaways

1. **Models Are Your Foundation**: Get them right from the start
2. **Serializers Are Powerful**: Use them for more than just JSON
3. **Authentication Matters**: Token auth is simple and effective
4. **Optimize Early**: Use select_related and prefetch_related
5. **Test Everything**: Unit tests catch bugs before production

---

**Coming up: Part 3 - Next.js Frontend Architecture**

*Questions? Comments? Let me know what you'd like to see in the next post!*
