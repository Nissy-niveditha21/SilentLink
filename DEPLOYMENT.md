# Deployment Guide for SilentLink

This guide provides comprehensive deployment instructions for SilentLink, an ASL (American Sign Language) recognition platform.

## Deployment Options

### 1. Local Development (Quick Start)

#### Windows
```powershell
.\Run-SilentLink.ps1
```

#### macOS/Linux/Manual
```bash
python -m venv veenv
source veenv/bin/activate  # Windows: veenv\Scripts\activate
pip install -r requirements.txt
[ ! -f .env ] && cp .env.example .env
python run.py
```

Open http://127.0.0.1:8000 in your browser.

### 2. Docker Deployment (Recommended for Production)

#### Prerequisites
- Docker and Docker Compose installed
- `.env.production` file configured (use `.env.production.example` as template)

#### Steps
1. **Configure environment variables**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with your production values
   # SECRET_KEY must be a strong random string
   ```

2. **Build and run with Docker Compose**
   ```bash
   # Linux/macOS
   chmod +x deploy.sh
   ./deploy.sh
   
   # Windows PowerShell
   .\deploy.ps1
   ```

   Or manually:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. **Access the application**
   - Main application: http://localhost:8000
   - API documentation: http://localhost:8000/api/docs
   - Health check: http://localhost:8000/health

#### Docker Commands
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Update the application
docker-compose build --no-cache
docker-compose up -d
```

### 3. Render Deployment (Cloud)

SilentLink includes a `render.yaml` blueprint for Render.com deployment.

#### Steps
1. Push the repository to GitHub
2. In Render, select **New → Blueprint**
3. Connect your repository
4. Render will automatically:
   - Create a web service from the blueprint
   - Install dependencies from `requirements.txt`
   - Set up persistent storage for SQLite database
   - Generate a secure `SECRET_KEY`
   - Deploy the application

#### Render Configuration
- **Service Type**: Web Service
- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

### 4. Vercel Deployment

For Vercel deployment, use the included `vercel.json` configuration.

#### Steps
1. Push repository to GitHub
2. Import in Vercel with **Add New → Project**
3. Set framework preset to **Other**
4. Configure environment variables in Vercel dashboard:
   - `SECRET_KEY`: Generate a strong random secret
   - `DATABASE_URL`: Use managed PostgreSQL (Neon, Supabase, etc.)
   - `SESSION_COOKIE_SECURE`: `true`

## Environment Variables

### Required Variables
| Variable | Description | Default | Production Value |
|----------|-------------|---------|------------------|
| `SECRET_KEY` | Session encryption key | `GENERATE-ME` | Strong random string (min 32 chars) |
| `DATABASE_URL` | Database connection URL | `sqlite:///data/silentlink.db` | PostgreSQL for production |
| `HOST` | Server host binding | `127.0.0.1` | `0.0.0.0` |
| `PORT` | Server port | `8000` | `8000` or `$PORT` |
| `SESSION_COOKIE_NAME` | Session cookie name | `silentlink_session` | `silentlink_session` |
| `SESSION_COOKIE_SECURE` | Secure cookies | `false` | `true` (HTTPS required) |

### Generating SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Database Configuration

### Development (SQLite)
- Default: `sqlite:///data/silentlink.db`
- File persists in `data/` directory
- Suitable for single-instance deployments

### Production (PostgreSQL Recommended)
- Use managed PostgreSQL services:
  - Neon (neon.tech)
  - Supabase (supabase.com)
  - AWS RDS
  - Google Cloud SQL
- Connection URL format: `postgresql://user:password@host:port/database`

## Security Considerations

### 1. Secrets Management
- Never commit `.env` or `.env.production` files
- Use environment variables in production
- Rotate `SECRET_KEY` periodically

### 2. HTTPS Requirements
- Set `SESSION_COOKIE_SECURE=true` for production
- Enable HTTPS on your domain
- Use trusted SSL certificates

### 3. CORS Configuration
If frontend is hosted separately:
```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring and Maintenance

### Health Checks
- Endpoint: `/health`
- Use for load balancers and monitoring

### Logs
- Application logs to stdout/stderr
- Use Docker logs: `docker-compose logs -f`
- Configure log aggregation for production

### Backup Strategy
1. **Database Backups**
   - Regular PostgreSQL backups
   - SQLite: Backup `data/silentlink.db` file

2. **Model Backups**
   - Backup `asl_model.h5` and `models/` directory
   - Version control for training configurations

## Scaling Considerations

### Horizontal Scaling
1. **Database**: Use PostgreSQL instead of SQLite
2. **Session Storage**: Use Redis for distributed sessions
3. **WebSockets**: Ensure WebSocket connections are properly managed

### Performance Tuning
1. **Uvicorn Workers**: Adjust based on CPU cores
   ```bash
   uvicorn backend.main:app --workers 4
   ```

2. **Database Connection Pool**: Configure SQLAlchemy pool size

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database URL format
   - Verify network connectivity
   - Ensure database is accessible

2. **ML Model Loading Issues**
   - Verify `asl_model.h5` exists
   - Check TensorFlow compatibility
   - Ensure sufficient memory

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify WebSocket support in deployment platform
   - Check client-side connectivity

4. **Camera Permission Issues**
   - HTTPS required for camera access
   - Check browser permissions
   - Verify MediaPipe initialization

### Log Analysis
Check logs for:
- Startup errors
- Database connection issues
- ML model loading errors
- WebSocket connection problems

## Updates and Maintenance

### Updating the Application
1. Pull latest changes
2. Rebuild Docker images:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Dependency Updates
1. Update `requirements.txt`
2. Rebuild containers
3. Test thoroughly before production deployment

## Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Review deployment platform documentation
4. Consult project documentation in README.md

## License
SilentLink is released under the MIT License. See LICENSE file for details.