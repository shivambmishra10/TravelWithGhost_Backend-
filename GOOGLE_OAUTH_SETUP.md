# Google OAuth Authentication Setup Guide

This guide explains how to set up Google OAuth 2.0 authentication for the travelwithghost application. Users can now log in or register using their Google accounts.

## Overview

The implementation uses:
- **Backend**: Django with `google-auth` and `google-auth-oauthlib` libraries
- **Frontend**: React with `@react-oauth/google` library
- **Auth Flow**: Google ID Token validation on backend

## Prerequisites

1. Google Cloud Console account
2. A Google OAuth 2.0 project configured
3. Client ID and Client Secret from Google

## Step 1: Set Up Google OAuth 2.0 Credentials

### A. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "NEW PROJECT"
3. Name your project (e.g., "travelwithghost") and click "Create"
4. Wait for the project to be created

### B. Enable Google+ API

1. In the Cloud Console, search for "Google+ API" in the top search bar
2. Click on it and select "ENABLE"
3. Similarly, enable "Identity Toolkit API"

### C. Create OAuth 2.0 Credentials

1. In the left sidebar, click **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **OAuth 2.0 Client ID**
3. If prompted, configure the OAuth consent screen:
   - **User Type**: External (for development/testing)
   - **App name**: travelwithghost
   - **User support email**: your-email@example.com
   - **Developer contact**: your-email@example.com
   - Click "Save and Continue"
4. **Scopes**: Click "Save and Continue" (no additional scopes needed for basic Google Sign-In)
5. **Test Users**: Add test email addresses if desired, click "Save and Continue"

### D. Create Web Application Credentials

1. Return to **Credentials** page
2. Click **"+ CREATE CREDENTIALS"** → **OAuth 2.0 Client ID**
3. **Application type**: Select "Web application"
4. **Name**: travelwithghost-web
5. **Authorized JavaScript origins**: Add your domain(s):
   - For development: `http://localhost:3000`
   - For staging: `https://your-staging-domain.com`
   - For production: `https://your-production-domain.com`
6. **Authorized redirect URIs**: Add:
   - `http://localhost:3000/login`
   - `https://your-staging-domain.com/login`
   - `https://your-production-domain.com/login`
   - `http://localhost:3000/register`
   - `https://your-staging-domain.com/register`
   - `https://your-production-domain.com/register`
7. Click **"Create"**
8. A popup will show your **Client ID** and **Client Secret**. Copy these values.

## Step 2: Configure Frontend Environment Variables

### A. Development Environment (`.env.local`)

```bash
# /frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### B. Production Environment (`.env.production`)

```bash
# /frontend/.env.production
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_SITE_URL=https://your-production-domain.com
```

**Important**: The `NEXT_PUBLIC_` prefix makes the variable accessible in the browser. It is **safe** to expose the Client ID (not the Secret).

## Step 3: Verify Backend Dependencies

Ensure the backend `requirements.txt` includes:
```
google-auth==2.28.1
google-auth-oauthlib==1.2.0
```

Install dependencies if not already installed:
```bash
cd backend
pip install -r requirements.txt
```

## Step 4: Backend Implementation

The backend has been configured with the following:

### New Endpoint
- **Route**: `POST /api/auth/google/`
- **Request Body**:
  ```json
  {
    "id_token": "GOOGLE_ID_TOKEN"
  }
  ```
- **Response**:
  ```json
  {
    "token": "AUTH_TOKEN",
    "user": {
      "id": 1,
      "username": "user@example.com",
      "email": "user@example.com",
      "profile": { ... }
    }
  }
  ```

### Flow
1. Frontend sends Google ID token from login/register
2. Backend validates token using `google.auth.transport.requests`
3. User is created or retrieved based on email
4. Auth token is generated and returned
5. User is automatically logged in

## Step 5: Frontend Implementation

The frontend has been configured with:

### 1. GoogleOAuthProvider in `_app.js`
```javascript
<GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}>
  <AuthProvider>
    <Component {...pageProps} />
  </AuthProvider>
</GoogleOAuthProvider>
```

### 2. Google Login Button in `/login` and `/register` pages
```javascript
<GoogleLogin
  onSuccess={handleGoogleSuccess}
  onError={handleGoogleError}
  text="signin_with" // or "signup_with" for register page
  size="large"
/>
```

### 3. Auth Context Method
```javascript
const googleLogin = async (idToken) => {
  const response = await api.post('/api/auth/google/', { id_token: idToken });
  // Token and user data stored and user logged in
}
```

## Step 6: Testing

### A. Local Development

1. Set up the backend:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Set up the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `http://localhost:3000/login` or `/register`
4. Click the Google sign-in/sign-up button
5. Complete Google authentication
6. You should be redirected to the home page or profile

### B. Test Users (Optional)

If your Google OAuth app is in development:
1. Go to Google Cloud Console → Credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Test users", add email addresses
4. Only those emails can use the app until you move to production

### C. Production Release

To allow all Google users to log in:
1. Go to Google Cloud Console → OAuth consent screen
2. Click **"PUBLISH APP"** to move from development to production

## Step 7: Deployment Configuration

### Frontend (Vercel)

1. Add environment variable in Vercel dashboard:
   - Go to **Settings** → **Environment Variables**
   - Add `NEXT_PUBLIC_GOOGLE_CLIENT_ID` with your production Google Client ID
   - Redeploy

### Backend (AWS EC2 / Docker)

No additional configuration needed. The backend validates any valid Google ID token.

## Troubleshooting

### Common Errors

1. **"Invalid Client ID"**
   - Verify `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set correctly
   - Check that the domain is in "Authorized JavaScript origins"

2. **"Invalid token"**
   - Ensure Google libraries are installed: `pip install google-auth google-auth-oauthlib`
   - Check backend logs for validation errors

3. **"CORS error"**
   - Ensure frontend domain is in `Authorized JavaScript origins` in Google Cloud
   - Check CORS settings in Django: `CORS_ALLOWED_ORIGINS` in `settings.py`

4. **User not created after login**
   - Check that the Google token contains `email` field
   - Verify database migrations are applied

### Debug Mode

Enable detailed logging in backend:
```python
# In config/settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

## Security Considerations

1. **Never expose Client Secret** in frontend code
2. **Always use HTTPS** in production
3. **Validate tokens** on the backend (already implemented)
4. **Store tokens securely** in localStorage (browser standard)
5. **Set secure cookie flags** (already configured in Django)

## Next Steps

1. Get your Google OAuth credentials from Google Cloud Console
2. Add `NEXT_PUBLIC_GOOGLE_CLIENT_ID` to `.env.local` and `.env.production`
3. Test login/register with Google on your local environment
4. Deploy frontend to Vercel with the production Client ID
5. Monitor logs for any authentication errors

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/gsi/web)
- [React OAuth Google Library](https://github.com/MomenSherif/react-oauth)
- [Django Google Authentication](https://django-allauth.readthedocs.io/)
