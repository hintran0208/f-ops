# F-Ops Frontend

React-based Web UI for the F-Ops DevOps Assistant.

## Features

### 🚀 Pipeline Agent
- **File Upload**: Upload project files or folders for analysis
- **Repository Analysis**: Enter GitHub/GitLab URLs for automatic stack detection
- **Pipeline Generation**: Generate GitHub Actions, GitLab CI, or Jenkins pipelines
- **Inline Editor**: Edit generated pipeline files directly in the browser
- **Copy & Save**: Copy pipeline content or save changes locally
- **Security Scanning**: Automatic integration of security scans and best practices

### 🏗️ Infrastructure Agent
- **Multi-Platform Support**: Kubernetes, Serverless, Static Sites, Docker, VMs
- **Terraform Generation**: Complete infrastructure modules with dry-run validation
- **Helm Charts**: Kubernetes deployments with lint checking and dry-run
- **Environment Configuration**: Staging and production environment setup
- **Dry-Run Validation**: Preview changes before deployment

### 📚 Knowledge Base
- **Source Connection**: Connect GitHub repos, documentation sites, wikis
- **Smart Search**: Semantic search across indexed knowledge sources
- **Citation Tracking**: All generated content includes knowledge base citations

## Quick Start

1. **Start Backend Server** (in separate terminal):
   ```bash
   cd ../backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend Development Server**:
   ```bash
   npm install
   npm run dev
   ```

3. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

### Pipeline Agent Workflow

1. **Upload Files** (optional): Drag and drop project files or folders
2. **Enter Repository URL**: GitHub/GitLab repository for analysis
3. **Configure Settings**:
   - Target platform (k8s, serverless, static, docker, vm)
   - Environments (staging, prod)
   - Technology stack (auto-detect or manual)
   - Organization standards (default, enterprise, startup, etc.)
4. **Generate Pipeline**: Click "Generate CI/CD Pipeline"
5. **Review Results**: View generated pipeline files with security scans
6. **Edit & Save**: Use inline editor to modify pipeline files
7. **Create PR**: Generate pull request with pipeline files

### Infrastructure Agent Workflow

1. **Select Target Platform**: Choose deployment target
2. **Configure Environment**: Set up staging/production environments
3. **Specify Details**: Domain, container registry, secrets strategy
4. **Generate Infrastructure**: Create Terraform and Helm configurations
5. **Review Dry-Run**: Examine Terraform plan and Helm dry-run results
6. **Create PR**: Generate pull request with infrastructure code

### File Operations

- **Copy to Clipboard**: Click copy icon on any generated file
- **Edit Inline**: Click edit icon to modify files in the browser
- **Save Changes**: Use Save button to persist modifications
- **Download**: Right-click and save generated files locally

## Architecture

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Build Tool**: Vite for fast development and hot reloading
- **State Management**: React Query for server state management
- **UI Components**: Heroicons for consistent iconography
- **Form Handling**: React Hook Form for validation and submission
- **API Communication**: Fetch API with error handling and loading states

## Development

### File Structure
```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main application layout
│   ├── LoadingSpinner.tsx
│   ├── TerraformPlanViewer.tsx
│   └── HelmDryRunViewer.tsx
├── modules/            # Main feature modules
│   ├── PipelineModule.tsx      # Pipeline Agent UI
│   ├── InfrastructureModule.tsx # Infrastructure Agent UI
│   └── KBConnectModule.tsx     # Knowledge Base UI
├── services/           # API service layer
│   └── api.ts         # HTTP client and API definitions
└── main.tsx           # Application entry point
```

### API Integration

All API calls go through the `services/api.ts` module with:
- Type-safe interfaces for requests/responses
- Error handling with custom ApiError class
- Loading states and retry logic
- Automatic request/response transformation

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom Components**: Reusable button, card, and form styles
- **Color Scheme**: F-Ops brand colors (f-ops-500, f-ops-600, etc.)
- **Responsive Design**: Mobile-first responsive layouts

## Production Deployment

### Docker Build
```bash
# Development
docker build -f Dockerfile -t fops-frontend:dev .

# Production
docker build -f Dockerfile.prod -t fops-frontend:prod .
```

### Docker Compose
```bash
# Development with backend
docker-compose up

# Production deployment
docker-compose -f docker-compose.prod.yml up
```

### Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Add proper error handling for API calls
4. Include loading states for user feedback
5. Test file upload and editing functionality
6. Ensure responsive design on mobile devices

## Troubleshooting

### Common Issues

1. **API Connection Failed**: Ensure backend server is running on port 8000
2. **File Upload Not Working**: Check file size limits and supported formats
3. **Edit Mode Issues**: Refresh page if inline editor becomes unresponsive
4. **CORS Errors**: Verify backend CORS configuration includes frontend URL

### Debug Mode

Enable debug mode by adding `?debug=true` to the URL for additional logging.