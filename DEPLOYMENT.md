# Deployment Guide 🚀

This guide will help you deploy the AI Study Assistant to production environments.

## 📋 Prerequisites

- Python 3.8+ installed
- Node.js 16+ installed
- Git installed
- A hosting service account (Heroku, Railway, Vercel, etc.)

## 🎯 Deployment Options

### Option 1: Full Stack on Railway (Recommended)

Railway provides excellent support for both Python and Node.js applications.

#### Backend Deployment

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Navigate to backend directory
   cd backend
   
   # Initialize Railway project
   railway init
   
   # Deploy
   railway up
   ```

3. **Configure Environment Variables**
   - In Railway dashboard, go to your project
   - Add environment variables:
     - `FLASK_ENV=production`
     - `PORT=5000`

#### Frontend Deployment

1. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Navigate to frontend directory
   cd frontend
   
   # Deploy
   vercel
   ```

2. **Configure Environment Variables**
   - In Vercel dashboard, add:
     - `VITE_API_URL=https://your-railway-backend-url.railway.app`

### Option 2: Heroku Deployment

#### Backend on Heroku

1. **Create Heroku App**
   ```bash
   # Install Heroku CLI
   # Create new app
   heroku create your-app-name-backend
   ```

2. **Configure for Python**
   ```bash
   # Add Python buildpack
   heroku buildpacks:set heroku/python
   
   # Add Procfile
   echo "web: gunicorn app:app" > Procfile
   ```

3. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy backend"
   git push heroku main
   ```

#### Frontend on Netlify

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Netlify**
   - Connect your GitHub repository
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Add environment variable: `VITE_API_URL=https://your-heroku-backend.herokuapp.com`

### Option 3: Docker Deployment

#### Backend Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:5000
```

## 🔧 Environment Configuration

### Backend Environment Variables

```bash
# Production settings
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///study_assistant.db

# AI Model Configuration
MODEL_CACHE_DIR=/tmp/models
MAX_CONTENT_LENGTH=16777216  # 16MB

# CORS Settings
CORS_ORIGINS=https://your-frontend-domain.com
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=https://your-backend-domain.com

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_VISUAL_QA=true
```

## 📊 Database Setup

### SQLite (Default)
No additional setup required for SQLite. The database will be created automatically.

### PostgreSQL (Production)
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update database URL
DATABASE_URL=postgresql://user:password@host:port/database
```

## 🔒 Security Considerations

### Backend Security
1. **CORS Configuration**
   ```python
   CORS(app, origins=["https://your-frontend-domain.com"])
   ```

2. **Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=get_remote_address)
   
   @app.route('/api/endpoint')
   @limiter.limit("10 per minute")
   def endpoint():
       pass
   ```

3. **Input Validation**
   - Validate all user inputs
   - Sanitize file uploads
   - Limit file sizes

### Frontend Security
1. **Environment Variables**
   - Never expose sensitive data in client-side code
   - Use build-time environment variables only

2. **Content Security Policy**
   ```html
   <meta http-equiv="Content-Security-Policy" 
         content="default-src 'self'; script-src 'self' 'unsafe-inline';">
   ```

## 📈 Monitoring and Logging

### Backend Monitoring
```python
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

app = Flask(__name__)
logger = logging.getLogger(__name__)
```

### Health Checks
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    }
```

## 🚀 Performance Optimization

### Backend Optimization
1. **Caching**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

2. **Database Indexing**
   ```sql
   CREATE INDEX idx_session_activity ON study_activities(session_id);
   CREATE INDEX idx_performance_timestamp ON flashcard_performance(timestamp);
   ```

### Frontend Optimization
1. **Code Splitting**
   ```typescript
   const LazyComponent = React.lazy(() => import('./LazyComponent'));
   ```

2. **Image Optimization**
   - Use WebP format
   - Implement lazy loading
   - Compress images

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          cd backend
          railway up

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          cd frontend
          vercel --token ${{ secrets.VERCEL_TOKEN }}
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check CORS configuration in backend
   - Verify frontend API URL

2. **Model Loading Issues**
   - Ensure sufficient memory allocation
   - Check model download permissions

3. **Database Connection**
   - Verify database URL format
   - Check connection permissions

### Debug Mode
```bash
# Backend debug
export FLASK_DEBUG=1
python app.py

# Frontend debug
npm run dev
```

## 📞 Support

For deployment issues:
1. Check the logs in your hosting platform
2. Verify environment variables
3. Test locally first
4. Check network connectivity

## 🎉 Success!

Once deployed, your AI Study Assistant will be available at your chosen domain. Users can:
- Access all study tools
- Track their progress
- Use visual question answering
- View analytics dashboard

Remember to monitor performance and user feedback to continuously improve the application!