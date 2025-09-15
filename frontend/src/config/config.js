// Backend URL Configuration
// This setup allows for different environments (development, staging, production)

// For cloud deployment (PRODUCTION)
const PRODUCTION_API_URL = 'https://your-cloud-backend.com';  // Replace with your actual deployed backend URL

// For local development (DEVELOPMENT)
// Try these alternatives if one doesn't work:
const DEVELOPMENT_API_URL = 'http://your-system-ip:8000';     // Alternative: localhost
// const DEVELOPMENT_API_URL = 'http://127.0.0.1:8000';    // Alternative: 127.0.0.1

// CONFIGURATION: Automatically use the appropriate URL based on environment
// For production builds, this will use the PRODUCTION_API_URL
// For development, this will use DEVELOPMENT_API_URL
export const BACKEND_URL = __DEV__ ? DEVELOPMENT_API_URL : PRODUCTION_API_URL;



// NOTE: When you deploy to production:
// 1. Update PRODUCTION_API_URL with your actual cloud service URL
// 2. Make sure your backend has proper CORS configuration
// 3. Run a production build of the app with: npm run build

// DEBUG: Uncomment the line below to see which URL is being used
console.log('Using backend URL:', BACKEND_URL);