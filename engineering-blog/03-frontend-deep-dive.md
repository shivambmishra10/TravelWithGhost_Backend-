# Building TravelWithGhost: Next.js Frontend Architecture

## Part 3: Frontend Deep Dive - Components, State, and User Experience

*Building a modern React frontend with Next.js*

---

## Introduction

In Parts 1 and 2, we covered the overall architecture and Django backend. Now, let's explore the Next.js frontend - the user-facing layer of TravelWithGhost. We'll dive into component structure, state management, API integration, and UI/UX decisions.

---

## Frontend Tech Stack

### Core Technologies
```
Next.js 14         → React framework with routing
React 18           → UI library
React Bootstrap    → UI components
Axios              → HTTP client
CSS Modules        → Scoped styling
```

### Why Next.js?

**Considered Alternatives**:
- Create React App (CRA)
- Vite + React
- Vanilla React

**Why I Chose Next.js**:
1. **File-based Routing**: `pages/` folder = automatic routing
2. **Built-in Optimizations**: Image optimization, code splitting
3. **Easy Deployment**: Vercel integration
4. **SEO-Friendly**: Server-side rendering capability
5. **Great DX**: Fast refresh, TypeScript support

---

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Navigation.js    # Header with auth
│   │   └── Chat.js          # Trip chat component
│   │
│   ├── contexts/            # React Context
│   │   └── AuthContext.js   # Global auth state
│   │
│   ├── pages/               # Next.js pages (routes)
│   │   ├── _app.js          # App wrapper
│   │   ├── index.js         # Home page (/)
│   │   ├── login.js         # Login page (/login)
│   │   ├── register.js      # Register page (/register)
│   │   ├── profile.js       # Profile page (/profile)
│   │   ├── manage-requests.js # Host requests (/manage-requests)
│   │   ├── cities/
│   │   │   └── [id].js      # City detail (/cities/1)
│   │   ├── trips/
│   │   │   ├── [id].js      # Trip detail (/trips/1)
│   │   │   └── create.js    # Create trip (/trips/create)
│   │   └── users/
│   │       └── [id].js      # User profile (/users/1)
│   │
│   ├── styles/              # CSS files
│   │   ├── globals.css      # Global styles
│   │   ├── landing.css      # Home page styles
│   │   ├── navigation.css   # Header styles
│   │   └── chat.css         # Chat styles
│   │
│   └── utils/               # Utilities
│       └── api.js           # Axios client
│
├── public/                  # Static assets
│   ├── logo.webp
│   └── default-avatar.svg
│
└── package.json             # Dependencies
```

---

## Core Concepts

### 1. **File-Based Routing**

Next.js automatically creates routes from the `pages/` directory:

```javascript
pages/index.js           →  /
pages/login.js           →  /login
pages/cities/[id].js     →  /cities/:id
pages/trips/create.js    →  /trips/create
```

**Dynamic Routes**:
```javascript
// pages/cities/[id].js
import { useRouter } from 'next/router';

export default function CityDetail() {
  const router = useRouter();
  const { id } = router.query;  // Access the dynamic parameter
  
  // Fetch city with this ID
  return <div>City ID: {id}</div>;
}
```

### 2. **API Client Setup**

**utils/api.js** - Centralized Axios instance:
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
});

// Add token to requests if it exists
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('token');
  if (token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  }
}

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized (token expired/invalid)
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        // Redirect to login
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${window.location.pathname}`;
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

**Why This Pattern?**:
- ✅ Single source of truth for API URL
- ✅ Automatic token injection
- ✅ Global error handling
- ✅ Easy to test and mock

### 3. **Authentication Context**

**contexts/AuthContext.js** - Global auth state:
```javascript
import { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Token ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/api/profile/');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const response = await api.post('/api/login/', { username, password });
    localStorage.setItem('token', response.data.token);
    api.defaults.headers.common['Authorization'] = `Token ${response.data.token}`;
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
```

**Usage in Components**:
```javascript
import { useAuth } from '../contexts/AuthContext';

function ProfilePage() {
  const { user, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!user) return <div>Please login</div>;
  
  return <div>Welcome, {user.username}!</div>;
}
```

---

## Key Pages Breakdown

### 1. **Home Page (index.js)**

**Structure**:
```javascript
export default function Home() {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCities() {
      try {
        const response = await api.get('/api/cities/');
        setCities(response.data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchCities();
  }, []);

  return (
    <div>
      <Navigation />
      
      {/* Hero Section */}
      <HeroSection />
      
      {/* Features Section */}
      <FeaturesSection />
      
      {/* Destinations Section */}
      <DestinationsSection cities={cities} loading={loading} />
    </div>
  );
}
```

**Key Features**:
- Fetches cities on mount
- Shows loading state
- Responsive design with Bootstrap
- Call-to-action buttons

**Hero Section**:
```javascript
<div className="bg-primary text-white py-5" style={{ 
  background: 'linear-gradient(135deg, #0a192f 0%, #112240 100%)',
  minHeight: '80vh',
  display: 'flex',
  alignItems: 'center'
}}>
  <Container>
    <Row className="align-items-center">
      <Col lg={6}>
        <h1 className="display-4 fw-bold mb-4">
          Discover New Places With New Friends
        </h1>
        <p className="lead mb-4">
          Join travel groups to your favorite destinations and 
          create unforgettable memories with like-minded travelers.
        </p>
        <div className="d-flex gap-3">
          <Link href="/trips/create">
            <Button variant="outline-light" size="lg">
              Create New Trip
            </Button>
          </Link>
          <Link href="#destinations">
            <Button variant="light" size="lg">
              Explore Destinations
            </Button>
          </Link>
        </div>
      </Col>
      <Col lg={6}>
        <img 
          src={`${process.env.NEXT_PUBLIC_API_URL}/media/hero.avif`}
          alt="Travel Adventure" 
          className="rounded-3 shadow-lg"
          style={{ width: '100%', objectFit: 'cover' }}
        />
      </Col>
    </Row>
  </Container>
</div>
```

### 2. **Login Page (login.js)**

**Form Handling**:
```javascript
export default function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(formData.username, formData.password);
      
      // Redirect to previous page or home
      const redirect = router.query.redirect || '/';
      router.push(redirect);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md={6}>
          <Card>
            <Card.Body>
              <h2 className="text-center mb-4">Login</h2>
              
              {error && (
                <Alert variant="danger">{error}</Alert>
              )}
              
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Username</Form.Label>
                  <Form.Control
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <Button 
                  type="submit" 
                  variant="primary" 
                  className="w-100"
                  disabled={loading}
                >
                  {loading ? 'Logging in...' : 'Login'}
                </Button>
              </Form>

              <div className="text-center mt-3">
                <p>
                  Don't have an account?{' '}
                  <Link href="/register">Register here</Link>
                </p>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
```

**Key Patterns**:
- Controlled form inputs
- Loading states
- Error handling
- Redirect after login
- Links to related pages

### 3. **Create Trip Page (trips/create.js)**

**Complex Form with Itinerary**:
```javascript
export default function CreateTrip() {
  const [cities, setCities] = useState([]);
  const [formData, setFormData] = useState({
    group_name: '',
    destination_id: '',
    start_date: '',
    end_date: '',
    description: '',
    min_age: 18,
    max_age: 99,
    required_members: 2
  });
  const [itinerary, setItinerary] = useState([
    { day: 1, description: '' }
  ]);

  // Fetch cities for dropdown
  useEffect(() => {
    async function fetchCities() {
      const response = await api.get('/api/cities/');
      setCities(response.data);
    }
    fetchCities();
  }, []);

  const handleAddDay = () => {
    setItinerary([
      ...itinerary,
      { day: itinerary.length + 1, description: '' }
    ]);
  };

  const handleItineraryChange = (index, value) => {
    const updated = [...itinerary];
    updated[index].description = value;
    setItinerary(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await api.post('/api/trips/', {
        ...formData,
        itinerary: itinerary
      });
      
      // Redirect to trip detail page
      router.push(`/trips/${response.data.id}`);
    } catch (error) {
      console.error('Error creating trip:', error);
      setError(error.response?.data?.error || 'Failed to create trip');
    }
  };

  return (
    <Container className="mt-5">
      <h2>Create New Trip</h2>
      
      <Form onSubmit={handleSubmit}>
        {/* Basic Info */}
        <Form.Group className="mb-3">
          <Form.Label>Group Name</Form.Label>
          <Form.Control
            type="text"
            name="group_name"
            value={formData.group_name}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Destination</Form.Label>
          <Form.Select
            name="destination_id"
            value={formData.destination_id}
            onChange={handleChange}
            required
          >
            <option value="">Select destination</option>
            {cities.map(city => (
              <option key={city.id} value={city.id}>
                {city.name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        {/* Date Range */}
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Start Date</Form.Label>
              <Form.Control
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                required
              />
            </Form.Group>
          </Col>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>End Date</Form.Label>
              <Form.Control
                type="date"
                name="end_date"
                value={formData.end_date}
                onChange={handleChange}
                required
              />
            </Form.Group>
          </Col>
        </Row>

        {/* Itinerary */}
        <h4 className="mt-4">Itinerary</h4>
        {itinerary.map((item, index) => (
          <Form.Group key={index} className="mb-3">
            <Form.Label>Day {item.day}</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={item.description}
              onChange={(e) => handleItineraryChange(index, e.target.value)}
              placeholder="What will you do on this day?"
              required
            />
          </Form.Group>
        ))}
        
        <Button 
          variant="outline-secondary" 
          onClick={handleAddDay}
          className="mb-3"
        >
          + Add Day
        </Button>

        <div className="d-grid">
          <Button type="submit" variant="primary" size="lg">
            Create Trip
          </Button>
        </div>
      </Form>
    </Container>
  );
}
```

**Complex Form Patterns**:
- Multiple related inputs
- Dynamic array (itinerary days)
- Dropdowns from API data
- Date pickers
- Nested object submission

### 4. **Trip Detail Page (trips/[id].js)**

**Data Fetching & Actions**:
```javascript
export default function TripDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTrip();
    }
  }, [id]);

  const fetchTrip = async () => {
    try {
      const response = await api.get(`/api/trips/${id}/`);
      setTrip(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinRequest = async () => {
    setRequesting(true);
    try {
      await api.post(`/api/trips/${id}/join/`);
      alert('Join request sent!');
      fetchTrip(); // Refresh trip data
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to send request');
    } finally {
      setRequesting(false);
    }
  };

  const isHost = user && trip && user.id === trip.host.id;
  const isMember = user && trip && trip.members.some(m => m.id === user.id);

  if (loading) return <Spinner />;
  if (!trip) return <div>Trip not found</div>;

  return (
    <Container className="mt-5">
      <Card>
        <Card.Img 
          variant="top" 
          src={`${process.env.NEXT_PUBLIC_API_URL}${trip.destination.image}`}
          height={300}
          style={{ objectFit: 'cover' }}
        />
        <Card.Body>
          <h2>{trip.group_name}</h2>
          <p className="text-muted">
            {trip.destination.name} • {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
          </p>
          
          <Card.Text>{trip.description}</Card.Text>

          {/* Host Info */}
          <div className="d-flex align-items-center mb-3">
            <img 
              src={trip.host.profile.photos || '/default-avatar.svg'}
              width={50}
              height={50}
              className="rounded-circle me-3"
            />
            <div>
              <strong>{trip.host.profile.name}</strong>
              <div className="text-muted small">Host</div>
            </div>
          </div>

          {/* Trip Stats */}
          <Row className="mb-4">
            <Col>
              <strong>Members:</strong> {trip.current_members_count}/{trip.required_members}
            </Col>
            <Col>
              <strong>Age Range:</strong> {trip.min_age} - {trip.max_age}
            </Col>
          </Row>

          {/* Itinerary */}
          <h4>Itinerary</h4>
          <ListGroup className="mb-4">
            {trip.itinerary_items.map((item) => (
              <ListGroup.Item key={item.day}>
                <strong>Day {item.day}:</strong> {item.description}
              </ListGroup.Item>
            ))}
          </ListGroup>

          {/* Members */}
          <h4>Members</h4>
          <Row>
            {trip.members.map((member) => (
              <Col key={member.id} md={4} className="mb-3">
                <Card>
                  <Card.Body>
                    <img 
                      src={member.profile.photos || '/default-avatar.svg'}
                      width={60}
                      height={60}
                      className="rounded-circle mb-2"
                    />
                    <div>{member.profile.name}</div>
                    <small className="text-muted">
                      {member.profile.current_location}
                    </small>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {/* Actions */}
          <div className="d-grid gap-2">
            {!user && (
              <Button variant="primary" onClick={() => router.push('/login')}>
                Login to Join
              </Button>
            )}
            
            {user && !isHost && !isMember && (
              <Button 
                variant="primary" 
                onClick={handleJoinRequest}
                disabled={requesting}
              >
                {requesting ? 'Sending...' : 'Request to Join'}
              </Button>
            )}
            
            {isHost && (
              <Button variant="outline-primary" onClick={() => router.push('/manage-requests')}>
                Manage Requests
              </Button>
            )}
            
            {isMember && (
              <Button variant="success" disabled>
                Already a Member
              </Button>
            )}
          </div>
        </Card.Body>
      </Card>

      {/* Chat Section (if member) */}
      {(isHost || isMember) && (
        <Chat tripId={id} />
      )}
    </Container>
  );
}
```

**Complex UI Logic**:
- Conditional rendering based on user role
- Multiple API calls
- Nested data display
- Action buttons with loading states

---

## Reusable Components

### 1. **Navigation Component**

```javascript
// components/Navigation.js
import { useAuth } from '../contexts/AuthContext';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import Link from 'next/link';

export default function Navigation() {
  const { user, logout } = useAuth();

  return (
    <Navbar bg="dark" variant="dark" expand="lg">
      <Container>
        <Link href="/" passHref legacyBehavior>
          <Navbar.Brand>
            🌍 travelwithghost™
          </Navbar.Brand>
        </Link>
        
        <Navbar.Toggle />
        
        <Navbar.Collapse>
          <Nav className="ms-auto">
            <Link href="/" passHref legacyBehavior>
              <Nav.Link>Home</Nav.Link>
            </Link>
            
            {user ? (
              <>
                <Link href="/trips/create" passHref legacyBehavior>
                  <Nav.Link>Create Trip</Nav.Link>
                </Link>
                <Link href="/profile" passHref legacyBehavior>
                  <Nav.Link>Profile</Nav.Link>
                </Link>
                <Link href="/manage-requests" passHref legacyBehavior>
                  <Nav.Link>Requests</Nav.Link>
                </Link>
                <Button 
                  variant="outline-light" 
                  size="sm" 
                  onClick={logout}
                  className="ms-2"
                >
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link href="/login" passHref legacyBehavior>
                  <Nav.Link>Login</Nav.Link>
                </Link>
                <Link href="/register" passHref legacyBehavior>
                  <Button variant="primary" size="sm" className="ms-2">
                    Sign Up
                  </Button>
                </Link>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
```

### 2. **Chat Component**

```javascript
// components/Chat.js
import { useState, useEffect, useRef } from 'react';
import { Card, Form, Button, ListGroup } from 'react-bootstrap';
import api from '../utils/api';
import { useAuth } from '../contexts/AuthContext';

export default function Chat({ tripId }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchMessages();
    // Poll for new messages every 5 seconds
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [tripId]);

  useEffect(() => {
    // Scroll to bottom on new messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const response = await api.get(`/api/trips/${tripId}/chat/`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      await api.post(`/api/trips/${tripId}/chat/`, {
        message: newMessage
      });
      setNewMessage('');
      fetchMessages();
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <Card className="mt-4">
      <Card.Header>
        <h5>Trip Chat</h5>
      </Card.Header>
      <Card.Body style={{ height: '400px', overflowY: 'auto' }}>
        <ListGroup variant="flush">
          {messages.map((msg) => (
            <ListGroup.Item 
              key={msg.id}
              className={msg.user.id === user.id ? 'text-end' : ''}
            >
              <div className="d-flex align-items-start gap-2">
                {msg.user.id !== user.id && (
                  <img 
                    src={msg.user.profile.photos || '/default-avatar.svg'}
                    width={30}
                    height={30}
                    className="rounded-circle"
                  />
                )}
                <div className="flex-grow-1">
                  <div className="small text-muted">
                    {msg.user.profile.name} • {formatTime(msg.timestamp)}
                  </div>
                  <div>{msg.message}</div>
                </div>
              </div>
            </ListGroup.Item>
          ))}
          <div ref={messagesEndRef} />
        </ListGroup>
      </Card.Body>
      <Card.Footer>
        <Form onSubmit={handleSend}>
          <Form.Group className="d-flex gap-2">
            <Form.Control
              type="text"
              placeholder="Type a message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
            />
            <Button type="submit">Send</Button>
          </Form.Group>
        </Form>
      </Card.Footer>
    </Card>
  );
}
```

**Chat Features**:
- Auto-refresh (polling)
- Auto-scroll to bottom
- User avatars
- Timestamps
- Visual distinction for own messages

---

## State Management Patterns

### 1. **Local State (useState)**

For component-specific data:
```javascript
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');
const [formData, setFormData] = useState({ name: '', email: '' });
```

### 2. **Global State (Context)**

For app-wide data:
```javascript
const { user, loading, login, logout } = useAuth();
```

### 3. **URL State (Router)**

For shareable state:
```javascript
const router = useRouter();
const { id, tab } = router.query;  // /trips/5?tab=chat
```

### 4. **Server State (API)**

For data from backend:
```javascript
useEffect(() => {
  async function fetchData() {
    const response = await api.get('/api/trips/');
    setTrips(response.data);
  }
  fetchData();
}, []);
```

---

## Form Handling Patterns

### 1. **Controlled Components**

```javascript
const [formData, setFormData] = useState({ name: '', email: '' });

const handleChange = (e) => {
  setFormData({
    ...formData,
    [e.target.name]: e.target.value
  });
};

<Form.Control
  name="name"
  value={formData.name}
  onChange={handleChange}
/>
```

### 2. **Validation**

```javascript
const validateForm = () => {
  const errors = {};
  
  if (!formData.name.trim()) {
    errors.name = 'Name is required';
  }
  
  if (!formData.email.includes('@')) {
    errors.email = 'Invalid email';
  }
  
  if (formData.min_age >= formData.max_age) {
    errors.age = 'Max age must be greater than min age';
  }
  
  return errors;
};

const handleSubmit = (e) => {
  e.preventDefault();
  
  const errors = validateForm();
  if (Object.keys(errors).length > 0) {
    setErrors(errors);
    return;
  }
  
  // Submit form
};
```

### 3. **File Uploads**

```javascript
const [photo, setPhoto] = useState(null);
const [preview, setPreview] = useState(null);

const handleFileChange = (e) => {
  const file = e.target.files[0];
  setPhoto(file);
  
  // Show preview
  const reader = new FileReader();
  reader.onloadend = () => {
    setPreview(reader.result);
  };
  reader.readAsDataURL(file);
};

const handleSubmit = async (e) => {
  e.preventDefault();
  
  const formData = new FormData();
  formData.append('photo', photo);
  formData.append('name', name);
  
  await api.post('/api/profile/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};
```

---

## Styling Approach

### 1. **Bootstrap Components**

```javascript
import { Button, Card, Form, Alert } from 'react-bootstrap';

<Card>
  <Card.Body>
    <Button variant="primary">Click Me</Button>
  </Card.Body>
</Card>
```

### 2. **Custom CSS**

```css
/* styles/landing.css */
.hero-section {
  background: linear-gradient(135deg, #0a192f 0%, #112240 100%);
  min-height: 80vh;
}

.card-hover {
  transition: transform 0.3s ease;
}

.card-hover:hover {
  transform: translateY(-5px);
}
```

### 3. **Inline Styles**

For dynamic values:
```javascript
<div style={{ 
  background: trip.isPast ? '#ccc' : '#fff',
  opacity: loading ? 0.5 : 1 
}}>
```

---

## Performance Optimizations

### 1. **Code Splitting**

Next.js automatically code-splits by page:
```
index.js      → 50 KB
trips/[id].js → 40 KB
profile.js    → 30 KB
```

Each page only loads its own code!

### 2. **Image Optimization**

```javascript
// Before
<img src="/hero.jpg" />

// After (Next.js Image)
import Image from 'next/image';
<Image src="/hero.jpg" width={800} height={600} />
```

But we used regular `<img>` for simplicity with external API images.

### 3. **Lazy Loading**

```javascript
import dynamic from 'next/dynamic';

const Chat = dynamic(() => import('../components/Chat'), {
  loading: () => <p>Loading chat...</p>,
  ssr: false  // Don't render on server
});
```

### 4. **Memoization**

```javascript
import { useMemo } from 'react';

const sortedTrips = useMemo(() => {
  return trips.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}, [trips]);
```

---

## Error Handling

### 1. **API Errors**

```javascript
try {
  const response = await api.get('/api/trips/');
  setTrips(response.data);
} catch (error) {
  if (error.response) {
    // Server responded with error
    setError(error.response.data.error);
  } else if (error.request) {
    // No response received
    setError('Network error. Please check your connection.');
  } else {
    // Other errors
    setError('An unexpected error occurred.');
  }
}
```

### 2. **User Feedback**

```javascript
const [alert, setAlert] = useState(null);

const showAlert = (message, type = 'success') => {
  setAlert({ message, type });
  setTimeout(() => setAlert(null), 3000);
};

{alert && (
  <Alert variant={alert.type} dismissible>
    {alert.message}
  </Alert>
)}
```

### 3. **Loading States**

```javascript
if (loading) {
  return (
    <Container className="text-center mt-5">
      <Spinner animation="border" role="status">
        <span className="visually-hidden">Loading...</span>
      </Spinner>
    </Container>
  );
}
```

---

## User Experience Enhancements

### 1. **Redirect After Login**

```javascript
// Login page
const redirect = router.query.redirect || '/';
await login(username, password);
router.push(redirect);

// Protected page
if (!user) {
  router.push(`/login?redirect=${router.pathname}`);
}
```

### 2. **Confirmation Dialogs**

```javascript
const handleDelete = () => {
  if (window.confirm('Are you sure you want to delete this trip?')) {
    deleteTrip();
  }
};
```

### 3. **Optimistic Updates**

```javascript
const handleLike = async () => {
  // Update UI immediately
  setLiked(true);
  
  try {
    await api.post(`/api/trips/${id}/like/`);
  } catch (error) {
    // Revert on error
    setLiked(false);
  }
};
```

---

## Deployment Configuration

### **vercel.json** (Optional)

```json
{
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.travelwithghost.com/api/:path*"
    }
  ]
}
```

### **next.config.mjs**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
    domains: ['api.travelwithghost.com', 'localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'api.travelwithghost.com',
        pathname: '/media/**',
      },
    ],
  },
};

export default nextConfig;
```

---

## Testing Approach

### **Manual Testing Checklist**

```markdown
- [ ] Home page loads
- [ ] Cities display with images
- [ ] Login works
- [ ] Register creates user
- [ ] Create trip form submits
- [ ] Trip detail shows correctly
- [ ] Join request sends
- [ ] Host can accept/reject
- [ ] Chat sends messages
- [ ] Profile updates
- [ ] Logout works
- [ ] Auth redirects work
- [ ] Error messages display
- [ ] Loading states show
```

---

## Common Patterns Summary

### 1. **Data Fetching**
```javascript
useEffect(() => {
  async function fetch() {
    const res = await api.get('/endpoint');
    setData(res.data);
  }
  fetch();
}, [dependencies]);
```

### 2. **Form Submission**
```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  await api.post('/endpoint', formData);
  router.push('/success');
};
```

### 3. **Conditional Rendering**
```javascript
{loading && <Spinner />}
{error && <Alert variant="danger">{error}</Alert>}
{data && <DisplayData data={data} />}
```

### 4. **Lists**
```javascript
{items.map(item => (
  <Card key={item.id}>
    {item.name}
  </Card>
))}
```

---

## Challenges & Solutions

### Challenge 1: Image URLs in Production

**Problem**: Hardcoded `localhost:8000`

**Solution**: Environment variables
```javascript
src={`${process.env.NEXT_PUBLIC_API_URL}${image}`}
```

### Challenge 2: Auth State Persistence

**Problem**: User logged out on refresh

**Solution**: Load user from localStorage on mount
```javascript
useEffect(() => {
  const token = localStorage.getItem('token');
  if (token) {
    fetchUser();
  }
}, []);
```

### Challenge 3: CORS Errors

**Problem**: API blocked by CORS policy

**Solution**: Configure Django CORS + Nginx headers

---

## What's Next?

In **Part 4**, we'll cover:
- Docker containerization
- Docker Compose orchestration
- AWS deployment
- Nginx configuration
- SSL setup

---

## Key Takeaways

1. **Next.js simplifies routing** with file-based system
2. **Context API works great** for auth state
3. **Controlled components** make forms predictable
4. **Error handling matters** for good UX
5. **Environment variables** are essential for deployment

---

**Coming up: Part 4 - Docker & Deployment**

*Questions? Let me know in the comments what you'd like explained further!*
