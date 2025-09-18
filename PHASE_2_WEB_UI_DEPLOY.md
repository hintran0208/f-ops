# Phase 2: Web UI & Deployment Implementation

## Duration: Week 2 (5 days)

## Objectives
- Build Web UI MVP with React and Tailwind CSS
- Implement onboarding wizard with live preview
- Create deployment workflows with approval system
- Integrate CI/CD pipeline generation
- Establish OPA policy enforcement

## Prerequisites from Phase 1
- ✅ FastAPI backend operational
- ✅ Chroma knowledge base configured
- ✅ Basic CLI commands working
- ✅ MCP packs foundation ready
- ✅ Authentication system in place

## Day-by-Day Breakdown

### Day 6: React Frontend Setup & Authentication

#### Morning (4 hours)
1. **React Project Initialization**
   ```bash
   # frontend/
   npm create vite@latest f-ops-ui -- --template react-ts
   cd f-ops-ui
   npm install
   ```

2. **Dependencies Installation**
   ```json
   {
     "dependencies": {
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "react-router-dom": "^6.20.0",
       "@reduxjs/toolkit": "^2.0.0",
       "react-redux": "^9.0.0",
       "axios": "^1.6.0",
       "@tanstack/react-query": "^5.0.0",
       "react-hook-form": "^7.48.0",
       "zod": "^3.22.0",
       "@headlessui/react": "^1.7.0",
       "@heroicons/react": "^2.0.0",
       "react-markdown": "^9.0.0",
       "react-syntax-highlighter": "^15.5.0",
       "recharts": "^2.10.0",
       "date-fns": "^3.0.0",
       "clsx": "^2.0.0"
     },
     "devDependencies": {
       "@types/react": "^18.2.0",
       "@types/react-dom": "^18.2.0",
       "@vitejs/plugin-react": "^4.2.0",
       "tailwindcss": "^3.3.0",
       "autoprefixer": "^10.4.0",
       "postcss": "^8.4.0",
       "typescript": "^5.3.0",
       "vite": "^5.0.0",
       "eslint": "^8.55.0",
       "prettier": "^3.1.0"
     }
   }
   ```

3. **Tailwind CSS Configuration**
   ```javascript
   // tailwind.config.js
   export default {
     content: [
       "./index.html",
       "./src/**/*.{js,ts,jsx,tsx}",
     ],
     theme: {
       extend: {
         colors: {
           primary: {
             50: '#eff6ff',
             500: '#3b82f6',
             600: '#2563eb',
             700: '#1d4ed8',
             900: '#1e3a8a',
           }
         },
         animation: {
           'spin-slow': 'spin 3s linear infinite',
           'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
         }
       },
     },
     plugins: [
       require('@tailwindcss/forms'),
       require('@tailwindcss/typography'),
     ],
   }
   ```

4. **Project Structure**
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── common/
   │   │   │   ├── Button.tsx
   │   │   │   ├── Card.tsx
   │   │   │   └── Modal.tsx
   │   │   ├── onboarding/
   │   │   │   ├── OnboardingWizard.tsx
   │   │   │   ├── RepositoryForm.tsx
   │   │   │   └── PreviewDiff.tsx
   │   │   ├── deployments/
   │   │   │   ├── DeploymentList.tsx
   │   │   │   ├── DeploymentDetails.tsx
   │   │   │   └── LiveLogs.tsx
   │   │   ├── incidents/
   │   │   │   ├── IncidentDashboard.tsx
   │   │   │   └── RCAView.tsx
   │   │   └── knowledge/
   │   │       ├── KnowledgeSearch.tsx
   │   │       └── SourceConnector.tsx
   │   ├── pages/
   │   │   ├── Dashboard.tsx
   │   │   ├── Onboarding.tsx
   │   │   ├── Deployments.tsx
   │   │   ├── Incidents.tsx
   │   │   └── KnowledgeBase.tsx
   │   ├── services/
   │   │   ├── api.ts
   │   │   ├── auth.ts
   │   │   └── websocket.ts
   │   ├── store/
   │   │   ├── index.ts
   │   │   ├── authSlice.ts
   │   │   └── deploymentSlice.ts
   │   ├── hooks/
   │   │   ├── useAuth.ts
   │   │   └── useWebSocket.ts
   │   ├── utils/
   │   ├── types/
   │   ├── App.tsx
   │   └── main.tsx
   └── public/
   ```

#### Afternoon (4 hours)
1. **Authentication Implementation**
   ```typescript
   // src/services/auth.ts
   import axios from 'axios';
   
   const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   
   export interface LoginCredentials {
     username: string;
     password: string;
   }
   
   export interface User {
     id: string;
     username: string;
     email: string;
     role: string;
   }
   
   class AuthService {
     async login(credentials: LoginCredentials): Promise<{ token: string; user: User }> {
       const response = await axios.post(`${API_URL}/api/auth/login`, credentials);
       if (response.data.token) {
         localStorage.setItem('token', response.data.token);
         localStorage.setItem('user', JSON.stringify(response.data.user));
       }
       return response.data;
     }
   
     logout(): void {
       localStorage.removeItem('token');
       localStorage.removeItem('user');
     }
   
     getCurrentUser(): User | null {
       const userStr = localStorage.getItem('user');
       return userStr ? JSON.parse(userStr) : null;
     }
   
     getToken(): string | null {
       return localStorage.getItem('token');
     }
   }
   
   export default new AuthService();
   ```

2. **Redux Store Setup**
   ```typescript
   // src/store/authSlice.ts
   import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
   import authService from '../services/auth';
   
   export const login = createAsyncThunk(
     'auth/login',
     async (credentials: LoginCredentials) => {
       return await authService.login(credentials);
     }
   );
   
   const authSlice = createSlice({
     name: 'auth',
     initialState: {
       user: authService.getCurrentUser(),
       isAuthenticated: !!authService.getToken(),
       loading: false,
       error: null,
     },
     reducers: {
       logout: (state) => {
         authService.logout();
         state.user = null;
         state.isAuthenticated = false;
       },
     },
     extraReducers: (builder) => {
       builder
         .addCase(login.pending, (state) => {
           state.loading = true;
           state.error = null;
         })
         .addCase(login.fulfilled, (state, action) => {
           state.loading = false;
           state.user = action.payload.user;
           state.isAuthenticated = true;
         })
         .addCase(login.rejected, (state, action) => {
           state.loading = false;
           state.error = action.error.message;
         });
     },
   });
   
   export const { logout } = authSlice.actions;
   export default authSlice.reducer;
   ```

3. **Main App Component**
   ```typescript
   // src/App.tsx
   import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
   import { Provider } from 'react-redux';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import { store } from './store';
   import Layout from './components/Layout';
   import Dashboard from './pages/Dashboard';
   import Onboarding from './pages/Onboarding';
   import Deployments from './pages/Deployments';
   import Incidents from './pages/Incidents';
   import KnowledgeBase from './pages/KnowledgeBase';
   import Login from './pages/Login';
   import PrivateRoute from './components/PrivateRoute';
   
   const queryClient = new QueryClient();
   
   function App() {
     return (
       <Provider store={store}>
         <QueryClientProvider client={queryClient}>
           <Router>
             <Routes>
               <Route path="/login" element={<Login />} />
               <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
                 <Route index element={<Navigate to="/dashboard" />} />
                 <Route path="dashboard" element={<Dashboard />} />
                 <Route path="onboarding" element={<Onboarding />} />
                 <Route path="deployments" element={<Deployments />} />
                 <Route path="incidents" element={<Incidents />} />
                 <Route path="knowledge" element={<KnowledgeBase />} />
               </Route>
             </Routes>
           </Router>
         </QueryClientProvider>
       </Provider>
     );
   }
   
   export default App;
   ```

### Day 7: Onboarding Wizard Implementation

#### Morning (4 hours)
1. **Onboarding Wizard Component**
   ```typescript
   // src/components/onboarding/OnboardingWizard.tsx
   import { useState } from 'react';
   import { useForm } from 'react-hook-form';
   import { zodResolver } from '@hookform/resolvers/zod';
   import * as z from 'zod';
   import RepositoryForm from './RepositoryForm';
   import StackDetection from './StackDetection';
   import ConfigurationOptions from './ConfigurationOptions';
   import PreviewDiff from './PreviewDiff';
   import ApprovalStep from './ApprovalStep';
   
   const steps = [
     { id: 'repository', name: 'Repository', component: RepositoryForm },
     { id: 'detection', name: 'Stack Detection', component: StackDetection },
     { id: 'configuration', name: 'Configuration', component: ConfigurationOptions },
     { id: 'preview', name: 'Preview Changes', component: PreviewDiff },
     { id: 'approval', name: 'Approval', component: ApprovalStep },
   ];
   
   export default function OnboardingWizard() {
     const [currentStep, setCurrentStep] = useState(0);
     const [wizardData, setWizardData] = useState({});
     
     const handleNext = (data: any) => {
       setWizardData({ ...wizardData, ...data });
       setCurrentStep(currentStep + 1);
     };
     
     const handleBack = () => {
       setCurrentStep(currentStep - 1);
     };
     
     const CurrentStepComponent = steps[currentStep].component;
     
     return (
       <div className="max-w-4xl mx-auto p-6">
         <div className="mb-8">
           <nav aria-label="Progress">
             <ol className="flex items-center">
               {steps.map((step, index) => (
                 <li key={step.id} className="relative flex-1">
                   <div className={`flex items-center ${
                     index <= currentStep ? 'text-primary-600' : 'text-gray-400'
                   }`}>
                     <span className={`flex h-10 w-10 items-center justify-center rounded-full ${
                       index < currentStep ? 'bg-primary-600' :
                       index === currentStep ? 'border-2 border-primary-600' :
                       'border-2 border-gray-300'
                     }`}>
                       {index < currentStep ? (
                         <CheckIcon className="h-6 w-6 text-white" />
                       ) : (
                         <span>{index + 1}</span>
                       )}
                     </span>
                     <span className="ml-4 text-sm font-medium">{step.name}</span>
                   </div>
                   {index < steps.length - 1 && (
                     <div className="absolute top-5 left-10 -right-10 h-0.5 bg-gray-200">
                       <div className={`h-full bg-primary-600 transition-all ${
                         index < currentStep ? 'w-full' : 'w-0'
                       }`} />
                     </div>
                   )}
                 </li>
               ))}
             </ol>
           </nav>
         </div>
         
         <div className="bg-white shadow rounded-lg p-6">
           <CurrentStepComponent
             data={wizardData}
             onNext={handleNext}
             onBack={handleBack}
             isFirstStep={currentStep === 0}
             isLastStep={currentStep === steps.length - 1}
           />
         </div>
       </div>
     );
   }
   ```

2. **Repository Form Component**
   ```typescript
   // src/components/onboarding/RepositoryForm.tsx
   import { useForm } from 'react-hook-form';
   import { zodResolver } from '@hookform/resolvers/zod';
   import * as z from 'zod';
   
   const schema = z.object({
     repoUrl: z.string().url('Must be a valid URL'),
     target: z.enum(['k8s', 'serverless', 'static']),
     environments: z.array(z.string()).min(1, 'Select at least one environment'),
     branch: z.string().optional(),
   });
   
   type FormData = z.infer<typeof schema>;
   
   export default function RepositoryForm({ data, onNext }) {
     const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
       resolver: zodResolver(schema),
       defaultValues: data,
     });
   
     const onSubmit = (formData: FormData) => {
       onNext(formData);
     };
   
     return (
       <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
         <div>
           <label className="block text-sm font-medium text-gray-700">
             Repository URL
           </label>
           <input
             type="url"
             {...register('repoUrl')}
             className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
             placeholder="https://github.com/your-org/your-repo"
           />
           {errors.repoUrl && (
             <p className="mt-1 text-sm text-red-600">{errors.repoUrl.message}</p>
           )}
         </div>
   
         <div>
           <label className="block text-sm font-medium text-gray-700">
             Deployment Target
           </label>
           <select
             {...register('target')}
             className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
           >
             <option value="k8s">Kubernetes</option>
             <option value="serverless">Serverless (Lambda/Functions)</option>
             <option value="static">Static Site</option>
           </select>
         </div>
   
         <div>
           <label className="block text-sm font-medium text-gray-700">
             Environments
           </label>
           <div className="mt-2 space-y-2">
             {['development', 'staging', 'production'].map((env) => (
               <label key={env} className="flex items-center">
                 <input
                   type="checkbox"
                   value={env}
                   {...register('environments')}
                   className="rounded border-gray-300 text-primary-600"
                 />
                 <span className="ml-2 text-sm text-gray-700">{env}</span>
               </label>
             ))}
           </div>
           {errors.environments && (
             <p className="mt-1 text-sm text-red-600">{errors.environments.message}</p>
           )}
         </div>
   
         <div className="flex justify-end">
           <button
             type="submit"
             className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
           >
             Next: Detect Stack
           </button>
         </div>
       </form>
     );
   }
   ```

#### Afternoon (4 hours)
1. **Stack Detection Component**
   ```typescript
   // src/components/onboarding/StackDetection.tsx
   import { useEffect, useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import api from '../../services/api';
   
   export default function StackDetection({ data, onNext, onBack }) {
     const [detectedStack, setDetectedStack] = useState(null);
     
     const { data: detection, isLoading, error } = useQuery({
       queryKey: ['detectStack', data.repoUrl],
       queryFn: () => api.post('/onboard/detect-stack', { repoUrl: data.repoUrl }),
     });
     
     useEffect(() => {
       if (detection) {
         setDetectedStack(detection.data);
       }
     }, [detection]);
     
     const handleConfirm = () => {
       onNext({ stack: detectedStack });
     };
     
     if (isLoading) {
       return (
         <div className="flex items-center justify-center h-64">
           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
           <span className="ml-3">Analyzing repository...</span>
         </div>
       );
     }
     
     return (
       <div className="space-y-6">
         <h3 className="text-lg font-medium">Detected Technology Stack</h3>
         
         {detectedStack && (
           <div className="bg-gray-50 rounded-lg p-4">
             <div className="grid grid-cols-2 gap-4">
               <div>
                 <h4 className="font-medium text-gray-700">Languages</h4>
                 <ul className="mt-2 space-y-1">
                   {detectedStack.languages.map((lang) => (
                     <li key={lang} className="flex items-center">
                       <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                       {lang}
                     </li>
                   ))}
                 </ul>
               </div>
               
               <div>
                 <h4 className="font-medium text-gray-700">Frameworks</h4>
                 <ul className="mt-2 space-y-1">
                   {detectedStack.frameworks.map((framework) => (
                     <li key={framework} className="flex items-center">
                       <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                       {framework}
                     </li>
                   ))}
                 </ul>
               </div>
               
               <div>
                 <h4 className="font-medium text-gray-700">Build Tools</h4>
                 <ul className="mt-2 space-y-1">
                   {detectedStack.buildTools.map((tool) => (
                     <li key={tool} className="flex items-center">
                       <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                       {tool}
                     </li>
                   ))}
                 </ul>
               </div>
               
               <div>
                 <h4 className="font-medium text-gray-700">Dependencies</h4>
                 <p className="mt-2 text-sm text-gray-600">
                   {detectedStack.dependencies.length} dependencies detected
                 </p>
               </div>
             </div>
           </div>
         )}
         
         <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
           <h4 className="font-medium text-blue-900">AI Recommendations</h4>
           <ul className="mt-2 space-y-2 text-sm text-blue-800">
             <li>• Suggested CI/CD: GitHub Actions with Docker</li>
             <li>• Recommended deployment strategy: Blue-Green deployment</li>
             <li>• Security scanning: SAST with SonarQube, DAST with OWASP ZAP</li>
             <li>• Monitoring: Prometheus + Grafana stack</li>
           </ul>
         </div>
         
         <div className="flex justify-between">
           <button
             onClick={onBack}
             className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
           >
             Back
           </button>
           <button
             onClick={handleConfirm}
             className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
           >
             Next: Configure
           </button>
         </div>
       </div>
     );
   }
   ```

2. **Preview Diff Component**
   ```typescript
   // src/components/onboarding/PreviewDiff.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import ReactDiffViewer from 'react-diff-viewer';
   import api from '../../services/api';
   
   export default function PreviewDiff({ data, onNext, onBack }) {
     const [selectedFile, setSelectedFile] = useState(0);
     
     const { data: preview, isLoading } = useQuery({
       queryKey: ['preview', data],
       queryFn: () => api.post('/onboard/generate-preview', data),
     });
     
     if (isLoading) {
       return (
         <div className="flex items-center justify-center h-64">
           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
           <span className="ml-3">Generating configuration...</span>
         </div>
       );
     }
     
     const files = preview?.data?.files || [];
     
     return (
       <div className="space-y-4">
         <h3 className="text-lg font-medium">Preview Generated Configuration</h3>
         
         <div className="flex space-x-4">
           <div className="w-1/4">
             <h4 className="font-medium text-sm text-gray-700 mb-2">Files to be created</h4>
             <ul className="space-y-1">
               {files.map((file, index) => (
                 <li
                   key={file.path}
                   onClick={() => setSelectedFile(index)}
                   className={`cursor-pointer px-3 py-2 rounded text-sm ${
                     selectedFile === index
                       ? 'bg-primary-100 text-primary-700'
                       : 'hover:bg-gray-100'
                   }`}
                 >
                   {file.path}
                 </li>
               ))}
             </ul>
           </div>
           
           <div className="flex-1">
             {files[selectedFile] && (
               <div className="border rounded-lg overflow-hidden">
                 <div className="bg-gray-100 px-4 py-2 border-b">
                   <span className="font-mono text-sm">{files[selectedFile].path}</span>
                 </div>
                 <ReactDiffViewer
                   oldValue=""
                   newValue={files[selectedFile].content}
                   splitView={false}
                   showDiffOnly={false}
                   styles={{
                     contentText: { fontSize: '14px' }
                   }}
                 />
               </div>
             )}
           </div>
         </div>
         
         <div className="flex justify-between">
           <button
             onClick={onBack}
             className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
           >
             Back
           </button>
           <button
             onClick={() => onNext({ preview: files })}
             className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
           >
             Next: Approve & Deploy
           </button>
         </div>
       </div>
     );
   }
   ```

### Day 8: Deployment Workflows & Live Logs

#### Morning (4 hours)
1. **Deployment List Component**
   ```typescript
   // src/pages/Deployments.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import DeploymentList from '../components/deployments/DeploymentList';
   import DeploymentDetails from '../components/deployments/DeploymentDetails';
   import api from '../services/api';
   
   export default function Deployments() {
     const [selectedDeployment, setSelectedDeployment] = useState(null);
     
     const { data: deployments, isLoading } = useQuery({
       queryKey: ['deployments'],
       queryFn: () => api.get('/deployments'),
       refetchInterval: 5000, // Auto-refresh every 5 seconds
     });
     
     return (
       <div className="container mx-auto px-4 py-8">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-2xl font-bold">Deployments</h1>
           <button className="px-4 py-2 bg-primary-600 text-white rounded-md">
             New Deployment
           </button>
         </div>
         
         <div className="grid grid-cols-12 gap-6">
           <div className="col-span-4">
             <DeploymentList
               deployments={deployments?.data || []}
               selectedId={selectedDeployment?.id}
               onSelect={setSelectedDeployment}
               isLoading={isLoading}
             />
           </div>
           
           <div className="col-span-8">
             {selectedDeployment ? (
               <DeploymentDetails deployment={selectedDeployment} />
             ) : (
               <div className="bg-gray-50 rounded-lg p-12 text-center text-gray-500">
                 Select a deployment to view details
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

2. **Live Logs Component with WebSocket**
   ```typescript
   // src/components/deployments/LiveLogs.tsx
   import { useEffect, useState, useRef } from 'react';
   import useWebSocket from '../../hooks/useWebSocket';
   
   export default function LiveLogs({ deploymentId }) {
     const [logs, setLogs] = useState<string[]>([]);
     const logsEndRef = useRef<HTMLDivElement>(null);
     const { socket, isConnected } = useWebSocket();
     
     useEffect(() => {
       if (socket && isConnected) {
         socket.emit('subscribe-logs', { deploymentId });
         
         socket.on('log-entry', (entry) => {
           setLogs((prev) => [...prev, entry]);
         });
         
         return () => {
           socket.emit('unsubscribe-logs', { deploymentId });
           socket.off('log-entry');
         };
       }
     }, [socket, isConnected, deploymentId]);
     
     useEffect(() => {
       logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
     }, [logs]);
     
     return (
       <div className="bg-gray-900 rounded-lg p-4">
         <div className="flex items-center justify-between mb-2">
           <h3 className="text-white font-medium">Live Logs</h3>
           <div className="flex items-center space-x-2">
             <div className={`w-2 h-2 rounded-full ${
               isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
             }`} />
             <span className="text-xs text-gray-400">
               {isConnected ? 'Connected' : 'Disconnected'}
             </span>
           </div>
         </div>
         
         <div className="bg-black rounded p-3 h-96 overflow-y-auto font-mono text-xs">
           {logs.map((log, index) => (
             <div key={index} className="text-green-400 whitespace-pre-wrap">
               {log}
             </div>
           ))}
           <div ref={logsEndRef} />
         </div>
       </div>
     );
   }
   ```

#### Afternoon (4 hours)
1. **Deployment Approval System**
   ```typescript
   // src/components/deployments/ApprovalModal.tsx
   import { useState } from 'react';
   import { useMutation } from '@tanstack/react-query';
   import api from '../../services/api';
   
   export default function ApprovalModal({ deployment, onClose, onApprove }) {
     const [comment, setComment] = useState('');
     const [requireSecondApproval, setRequireSecondApproval] = useState(false);
     
     const approveMutation = useMutation({
       mutationFn: (data) => api.post(`/deployments/${deployment.id}/approve`, data),
       onSuccess: () => {
         onApprove();
         onClose();
       },
     });
     
     const handleApprove = () => {
       approveMutation.mutate({
         comment,
         requireSecondApproval,
       });
     };
     
     return (
       <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
         <div className="bg-white rounded-lg p-6 max-w-lg w-full">
           <h2 className="text-lg font-bold mb-4">Approve Deployment</h2>
           
           <div className="mb-4">
             <h3 className="font-medium mb-2">Deployment Summary</h3>
             <div className="bg-gray-50 rounded p-3 text-sm">
               <p><strong>Service:</strong> {deployment.service}</p>
               <p><strong>Environment:</strong> {deployment.environment}</p>
               <p><strong>Version:</strong> {deployment.version}</p>
               <p><strong>Changes:</strong> {deployment.changesSummary}</p>
             </div>
           </div>
           
           <div className="mb-4">
             <h3 className="font-medium mb-2">Dry Run Results</h3>
             <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
               <p className="text-green-800">✓ All checks passed</p>
               <ul className="mt-2 space-y-1 text-green-700">
                 <li>• Policy validation: Passed</li>
                 <li>• Resource availability: Sufficient</li>
                 <li>• Dependencies: All healthy</li>
                 <li>• Estimated rollout time: 5 minutes</li>
               </ul>
             </div>
           </div>
           
           <div className="mb-4">
             <label className="block text-sm font-medium mb-2">
               Approval Comment
             </label>
             <textarea
               value={comment}
               onChange={(e) => setComment(e.target.value)}
               className="w-full border rounded-md p-2"
               rows={3}
               placeholder="Optional comment..."
             />
           </div>
           
           {deployment.environment === 'production' && (
             <div className="mb-4">
               <label className="flex items-center">
                 <input
                   type="checkbox"
                   checked={requireSecondApproval}
                   onChange={(e) => setRequireSecondApproval(e.target.checked)}
                   className="mr-2"
                 />
                 <span className="text-sm">Require second approval (recommended for production)</span>
               </label>
             </div>
           )}
           
           <div className="flex justify-end space-x-3">
             <button
               onClick={onClose}
               className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
             >
               Cancel
             </button>
             <button
               onClick={handleApprove}
               disabled={approveMutation.isPending}
               className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
             >
               {approveMutation.isPending ? 'Approving...' : 'Approve & Deploy'}
             </button>
           </div>
         </div>
       </div>
     );
   }
   ```

2. **Health Check Dashboard**
   ```typescript
   // src/components/deployments/HealthStatus.tsx
   import { useQuery } from '@tanstack/react-query';
   import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
   import api from '../../services/api';
   
   export default function HealthStatus({ deploymentId }) {
     const { data: health } = useQuery({
       queryKey: ['health', deploymentId],
       queryFn: () => api.get(`/deployments/${deploymentId}/health`),
       refetchInterval: 10000,
     });
     
     const getStatusColor = (status: string) => {
       switch (status) {
         case 'healthy': return 'text-green-500';
         case 'degraded': return 'text-yellow-500';
         case 'unhealthy': return 'text-red-500';
         default: return 'text-gray-500';
       }
     };
     
     return (
       <div className="bg-white rounded-lg shadow p-6">
         <h3 className="text-lg font-medium mb-4">Health Status</h3>
         
         <div className="grid grid-cols-3 gap-4 mb-6">
           <div className="text-center">
             <div className={`text-3xl font-bold ${getStatusColor(health?.data?.status)}`}>
               {health?.data?.status || 'Unknown'}
             </div>
             <div className="text-sm text-gray-500">Overall Status</div>
           </div>
           
           <div className="text-center">
             <div className="text-3xl font-bold">
               {health?.data?.uptime || '0'}%
             </div>
             <div className="text-sm text-gray-500">Uptime</div>
           </div>
           
           <div className="text-center">
             <div className="text-3xl font-bold">
               {health?.data?.responseTime || '0'}ms
             </div>
             <div className="text-sm text-gray-500">Avg Response Time</div>
           </div>
         </div>
         
         <div className="h-64">
           <ResponsiveContainer width="100%" height="100%">
             <LineChart data={health?.data?.metrics || []}>
               <CartesianGrid strokeDasharray="3 3" />
               <XAxis dataKey="timestamp" />
               <YAxis />
               <Tooltip />
               <Line type="monotone" dataKey="cpu" stroke="#3b82f6" name="CPU %" />
               <Line type="monotone" dataKey="memory" stroke="#10b981" name="Memory %" />
               <Line type="monotone" dataKey="requests" stroke="#f59e0b" name="Requests/s" />
             </LineChart>
           </ResponsiveContainer>
         </div>
       </div>
     );
   }
   ```

### Day 9: CI/CD Pipeline Generation

#### Morning (4 hours)
1. **Pipeline Generator Backend**
   ```python
   # backend/app/core/pipeline_generator.py
   from typing import Dict, Any, List
   import yaml
   from jinja2 import Template
   
   class PipelineGenerator:
       def __init__(self):
           self.templates = self.load_templates()
       
       def generate_github_actions(self, config: Dict[str, Any]) -> str:
           template = Template(self.templates['github_actions'])
           return template.render(**config)
       
       def generate_gitlab_ci(self, config: Dict[str, Any]) -> str:
           template = Template(self.templates['gitlab_ci'])
           return template.render(**config)
       
       def generate_jenkins(self, config: Dict[str, Any]) -> str:
           template = Template(self.templates['jenkins'])
           return template.render(**config)
       
       def generate_terraform(self, config: Dict[str, Any]) -> str:
           """Generate Terraform configuration for infrastructure"""
           template = Template(self.templates['terraform'])
           return template.render(**config)
       
       def generate_helm_chart(self, config: Dict[str, Any]) -> Dict[str, str]:
           """Generate Helm chart for Kubernetes deployment"""
           files = {}
           files['Chart.yaml'] = self.render_helm_chart(config)
           files['values.yaml'] = self.render_helm_values(config)
           files['templates/deployment.yaml'] = self.render_helm_deployment(config)
           files['templates/service.yaml'] = self.render_helm_service(config)
           files['templates/ingress.yaml'] = self.render_helm_ingress(config)
           return files
   ```

2. **GitHub Actions Template**
   ```yaml
   # templates/github_actions.yaml.j2
   name: {{ pipeline_name }}
   
   on:
     push:
       branches: {{ branches | join(', ') }}
     pull_request:
       branches: {{ branches | join(', ') }}
   
   env:
     REGISTRY: {{ registry }}
     IMAGE_NAME: {{ image_name }}
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up {{ language }}
           uses: actions/setup-{{ language }}@v3
           with:
             {{ language }}-version: '{{ language_version }}'
         
         - name: Install dependencies
           run: {{ install_command }}
         
         - name: Run tests
           run: {{ test_command }}
         
         - name: Run security scan
           uses: aquasecurity/trivy-action@master
           with:
             scan-type: 'fs'
             scan-ref: '.'
   
     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Docker Buildx
           uses: docker/setup-buildx-action@v2
         
         - name: Log in to registry
           uses: docker/login-action@v2
           with:
             registry: {{ registry }}
             username: ${{ secrets.REGISTRY_USERNAME }}
             password: ${{ secrets.REGISTRY_PASSWORD }}
         
         - name: Build and push Docker image
           uses: docker/build-push-action@v4
           with:
             context: .
             push: true
             tags: {{ registry }}/{{ image_name }}:${{ github.sha }}
   
     deploy:
       needs: build
       runs-on: ubuntu-latest
       if: github.ref == 'refs/heads/main'
       steps:
         - name: Deploy to {{ environment }}
           run: |
             # Deployment commands based on target
             {% if target == 'k8s' %}
             kubectl set image deployment/{{ app_name }} {{ app_name }}={{ registry }}/{{ image_name }}:${{ github.sha }}
             {% elif target == 'serverless' %}
             serverless deploy --stage {{ environment }}
             {% elif target == 'static' %}
             aws s3 sync ./dist s3://{{ bucket_name }}
             {% endif %}
   ```

#### Afternoon (4 hours)
1. **OPA Policy Implementation**
   ```python
   # backend/app/core/policy_engine.py
   from opa_client import OpaClient
   import json
   from typing import Dict, Any, List
   
   class PolicyEngine:
       def __init__(self, opa_url: str = "http://localhost:8181"):
           self.client = OpaClient(opa_url)
           self.load_policies()
       
       def load_policies(self):
           """Load default policies"""
           policies = [
               self.deployment_window_policy(),
               self.approval_policy(),
               self.resource_limit_policy(),
               self.security_policy()
           ]
           
           for policy in policies:
               self.client.update_policy(policy['name'], policy['content'])
       
       def deployment_window_policy(self) -> Dict[str, str]:
           return {
               'name': 'deployment_window',
               'content': '''
               package deployment.window
               
               import future.keywords.if
               import future.keywords.in
               
               default allow = false
               
               # Allow deployments during business hours (9 AM - 6 PM UTC)
               allow if {
                   current_hour := time.clock([time.now_ns(), "UTC"])[0]
                   current_hour >= 9
                   current_hour <= 18
               }
               
               # Always allow staging deployments
               allow if {
                   input.environment == "staging"
               }
               
               # Require approval for production outside business hours
               allow if {
                   input.environment == "production"
                   input.has_approval == true
               }
               '''
           }
       
       def check_deployment_policy(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
           """Check if deployment meets policy requirements"""
           result = self.client.check_policy('deployment/window', deployment)
           
           if not result['allow']:
               return {
                   'allowed': False,
                   'reason': 'Deployment blocked by policy',
                   'violations': result.get('violations', [])
               }
           
           return {'allowed': True}
   ```

2. **Policy UI Component**
   ```typescript
   // src/components/policies/PolicyViewer.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import api from '../../services/api';
   
   export default function PolicyViewer() {
     const [selectedPolicy, setSelectedPolicy] = useState(null);
     
     const { data: policies } = useQuery({
       queryKey: ['policies'],
       queryFn: () => api.get('/policies'),
     });
     
     return (
       <div className="bg-white rounded-lg shadow">
         <div className="p-6 border-b">
           <h2 className="text-lg font-medium">Active Policies</h2>
         </div>
         
         <div className="flex">
           <div className="w-1/3 border-r">
             <ul className="divide-y">
               {policies?.data?.map((policy) => (
                 <li
                   key={policy.id}
                   onClick={() => setSelectedPolicy(policy)}
                   className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${
                     selectedPolicy?.id === policy.id ? 'bg-primary-50' : ''
                   }`}
                 >
                   <div className="font-medium">{policy.name}</div>
                   <div className="text-sm text-gray-500">{policy.description}</div>
                 </li>
               ))}
             </ul>
           </div>
           
           <div className="flex-1 p-6">
             {selectedPolicy ? (
               <div>
                 <h3 className="font-medium mb-4">{selectedPolicy.name}</h3>
                 <div className="bg-gray-50 rounded p-4">
                   <pre className="text-sm font-mono">{selectedPolicy.content}</pre>
                 </div>
                 
                 <div className="mt-4">
                   <h4 className="font-medium mb-2">Recent Evaluations</h4>
                   <table className="min-w-full divide-y divide-gray-200">
                     <thead>
                       <tr>
                         <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Time</th>
                         <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Resource</th>
                         <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Result</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-gray-200">
                       {selectedPolicy.evaluations?.map((eval) => (
                         <tr key={eval.id}>
                           <td className="px-4 py-2 text-sm">{eval.timestamp}</td>
                           <td className="px-4 py-2 text-sm">{eval.resource}</td>
                           <td className="px-4 py-2">
                             <span className={`px-2 py-1 text-xs rounded ${
                               eval.allowed
                                 ? 'bg-green-100 text-green-800'
                                 : 'bg-red-100 text-red-800'
                             }`}>
                               {eval.allowed ? 'Allowed' : 'Denied'}
                             </span>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               </div>
             ) : (
               <div className="text-center text-gray-500">
                 Select a policy to view details
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 10: Integration Testing & Polish

#### Morning (4 hours)
1. **End-to-End Testing**
   ```typescript
   // tests/e2e/onboarding.test.ts
   import { test, expect } from '@playwright/test';
   
   test.describe('Onboarding Flow', () => {
     test('should complete full onboarding process', async ({ page }) => {
       // Login
       await page.goto('http://localhost:3000/login');
       await page.fill('input[name="username"]', 'admin');
       await page.fill('input[name="password"]', 'password');
       await page.click('button[type="submit"]');
       
       // Navigate to onboarding
       await page.goto('http://localhost:3000/onboarding');
       
       // Step 1: Repository
       await page.fill('input[name="repoUrl"]', 'https://github.com/test/repo');
       await page.selectOption('select[name="target"]', 'k8s');
       await page.check('input[value="staging"]');
       await page.check('input[value="production"]');
       await page.click('button:has-text("Next: Detect Stack")');
       
       // Step 2: Stack Detection
       await page.waitForSelector('text=Detected Technology Stack');
       await expect(page.locator('text=Node.js')).toBeVisible();
       await page.click('button:has-text("Next: Configure")');
       
       // Step 3: Configuration
       await page.waitForSelector('text=Configuration Options');
       await page.click('button:has-text("Next: Preview")');
       
       // Step 4: Preview
       await page.waitForSelector('text=Preview Generated Configuration');
       await expect(page.locator('.diff-viewer')).toBeVisible();
       await page.click('button:has-text("Next: Approve")');
       
       // Step 5: Approval
       await page.waitForSelector('text=Ready to Deploy');
       await page.click('button:has-text("Create PR & Deploy")');
       
       // Verify success
       await expect(page.locator('text=Successfully created PR')).toBeVisible();
     });
   });
   ```

2. **Performance Optimization**
   ```typescript
   // src/utils/performance.ts
   import { lazy, Suspense } from 'react';
   
   // Lazy load heavy components
   export const LazyOnboardingWizard = lazy(() => 
     import('../components/onboarding/OnboardingWizard')
   );
   
   export const LazyDeploymentDetails = lazy(() => 
     import('../components/deployments/DeploymentDetails')
   );
   
   // API response caching
   export const cacheConfig = {
     staleTime: 5 * 60 * 1000, // 5 minutes
     cacheTime: 10 * 60 * 1000, // 10 minutes
     refetchOnWindowFocus: false,
   };
   
   // Debounce search inputs
   export function debounce<T extends (...args: any[]) => any>(
     func: T,
     wait: number
   ): (...args: Parameters<T>) => void {
     let timeout: NodeJS.Timeout;
     
     return (...args: Parameters<T>) => {
       clearTimeout(timeout);
       timeout = setTimeout(() => func(...args), wait);
     };
   }
   ```

#### Afternoon (4 hours)
1. **Dashboard Implementation**
   ```typescript
   // src/pages/Dashboard.tsx
   import { useQuery } from '@tanstack/react-query';
   import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
   import api from '../services/api';
   
   export default function Dashboard() {
     const { data: stats } = useQuery({
       queryKey: ['dashboard-stats'],
       queryFn: () => api.get('/dashboard/stats'),
     });
     
     const { data: recentActivity } = useQuery({
       queryKey: ['recent-activity'],
       queryFn: () => api.get('/dashboard/activity'),
     });
     
     return (
       <div className="container mx-auto px-4 py-8">
         <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
         
         <div className="grid grid-cols-4 gap-6 mb-8">
           <StatCard
             title="Total Deployments"
             value={stats?.data?.totalDeployments || 0}
             change="+12%"
             trend="up"
           />
           <StatCard
             title="Success Rate"
             value={`${stats?.data?.successRate || 0}%`}
             change="+5%"
             trend="up"
           />
           <StatCard
             title="Active Services"
             value={stats?.data?.activeServices || 0}
             change="0"
             trend="neutral"
           />
           <StatCard
             title="Incidents Today"
             value={stats?.data?.incidentsToday || 0}
             change="-2"
             trend="down"
           />
         </div>
         
         <div className="grid grid-cols-2 gap-6">
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-medium mb-4">Deployments Over Time</h2>
             <ResponsiveContainer width="100%" height={300}>
               <BarChart data={stats?.data?.deploymentHistory || []}>
                 <CartesianGrid strokeDasharray="3 3" />
                 <XAxis dataKey="date" />
                 <YAxis />
                 <Tooltip />
                 <Bar dataKey="success" fill="#10b981" />
                 <Bar dataKey="failed" fill="#ef4444" />
               </BarChart>
             </ResponsiveContainer>
           </div>
           
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-medium mb-4">Recent Activity</h2>
             <ul className="space-y-3">
               {recentActivity?.data?.map((activity) => (
                 <li key={activity.id} className="flex items-start">
                   <div className={`w-2 h-2 mt-1.5 rounded-full ${
                     activity.type === 'deployment' ? 'bg-blue-500' :
                     activity.type === 'incident' ? 'bg-red-500' :
                     'bg-gray-500'
                   }`} />
                   <div className="ml-3">
                     <p className="text-sm font-medium">{activity.title}</p>
                     <p className="text-xs text-gray-500">{activity.timestamp}</p>
                   </div>
                 </li>
               ))}
             </ul>
           </div>
         </div>
       </div>
     );
   }
   
   function StatCard({ title, value, change, trend }) {
     const getTrendColor = () => {
       if (trend === 'up') return 'text-green-600';
       if (trend === 'down') return 'text-red-600';
       return 'text-gray-600';
     };
     
     return (
       <div className="bg-white rounded-lg shadow p-6">
         <h3 className="text-sm font-medium text-gray-500">{title}</h3>
         <div className="mt-2 flex items-baseline">
           <p className="text-2xl font-semibold">{value}</p>
           <p className={`ml-2 text-sm ${getTrendColor()}`}>{change}</p>
         </div>
       </div>
     );
   }
   ```

2. **Error Handling & Loading States**
   ```typescript
   // src/components/common/ErrorBoundary.tsx
   import { Component, ErrorInfo, ReactNode } from 'react';
   
   interface Props {
     children: ReactNode;
     fallback?: ReactNode;
   }
   
   interface State {
     hasError: boolean;
     error?: Error;
   }
   
   export class ErrorBoundary extends Component<Props, State> {
     public state: State = {
       hasError: false,
     };
   
     public static getDerivedStateFromError(error: Error): State {
       return { hasError: true, error };
     }
   
     public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
       console.error('Uncaught error:', error, errorInfo);
       // Send to error tracking service
     }
   
     public render() {
       if (this.state.hasError) {
         return this.props.fallback || (
           <div className="min-h-screen flex items-center justify-center">
             <div className="text-center">
               <h1 className="text-2xl font-bold text-red-600 mb-4">
                 Oops! Something went wrong
               </h1>
               <p className="text-gray-600 mb-4">
                 {this.state.error?.message || 'An unexpected error occurred'}
               </p>
               <button
                 onClick={() => window.location.reload()}
                 className="px-4 py-2 bg-primary-600 text-white rounded-md"
               >
                 Reload Page
               </button>
             </div>
           </div>
         );
       }
   
       return this.props.children;
     }
   }
   ```

## Deliverables

### By End of Week 2:
1. ✅ React frontend with Tailwind CSS
2. ✅ Authentication and authorization system
3. ✅ Onboarding wizard with 5 steps
4. ✅ Deployment management interface
5. ✅ Live logs with WebSocket
6. ✅ CI/CD pipeline generation (GitHub Actions, GitLab CI)
7. ✅ OPA policy enforcement
8. ✅ Approval workflow system
9. ✅ Health monitoring dashboard
10. ✅ Responsive design for all screens

## Success Criteria

### Technical Metrics:
- Page load time < 2 seconds
- WebSocket connection stability > 99%
- UI responsiveness < 100ms
- Browser compatibility (Chrome, Firefox, Safari)
- Mobile responsive design

### Functional Metrics:
- Complete onboarding flow works end-to-end
- Deployments can be triggered and monitored
- Policies are enforced correctly
- Approvals workflow functions properly
- Live logs stream in real-time

## Next Phase Preview

Phase 3 will focus on:
- Incident management dashboard
- Advanced knowledge base features
- Learning path integration
- Performance optimization
- Enhanced monitoring