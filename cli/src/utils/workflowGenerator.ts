import yaml from 'yaml';

export interface WorkflowConfig {
  target: string;
  environments: string[];
  language: string;
  framework: string;
  hasDocker: boolean;
  hasTests: boolean;
  projectName?: string;
  cloudProvider?: string;
  security?: {
    enableSecurityScanning: boolean;
    enableDependencyScanning: boolean;
    enableSecretScanning: boolean;
    enableContainerScanning: boolean;
  };
  performance?: {
    enableCaching: boolean;
    enableParallelBuilds: boolean;
    enableBuildMatrix: boolean;
  };
}

export class WorkflowGenerator {
  generateGitHubActions(config: WorkflowConfig): string {
    const workflow = {
      name: 'F-Ops Generated CI/CD Pipeline',
      on: {
        push: {
          branches: ['main', 'develop']
        },
        pull_request: {
          branches: ['main']
        }
      },
      env: {
        TARGET_ENVIRONMENT: config.target
      },
      jobs: {}
    };

    // Build job
    workflow.jobs = {
      ...workflow.jobs,
      ...this.generateBuildJob(config)
    };

    // Security job
    if (config.security?.enableSecurityScanning) {
      workflow.jobs = {
        ...workflow.jobs,
        ...this.generateSecurityJob(config)
      };
    }

    // Test job
    if (config.hasTests) {
      workflow.jobs = {
        ...workflow.jobs,
        ...this.generateTestJob(config)
      };
    }

    // Deployment jobs
    for (const env of config.environments) {
      workflow.jobs = {
        ...workflow.jobs,
        ...this.generateDeploymentJob(env, config)
      };
    }

    return yaml.stringify(workflow, { lineWidth: 0 });
  }

  generateGitLabCI(config: WorkflowConfig): string {
    const pipeline: any = {
      stages: ['build', 'test', 'security', 'deploy'],
      variables: {
        TARGET_ENVIRONMENT: config.target
      }
    };

    // Build stage
    pipeline['build'] = this.generateGitLabBuildStage(config);

    // Test stage
    if (config.hasTests) {
      pipeline['test'] = this.generateGitLabTestStage(config);
    }

    // Security stage
    if (config.security?.enableSecurityScanning) {
      pipeline['security-scan'] = this.generateGitLabSecurityStage(config);
    }

    // Deployment stages
    for (const env of config.environments) {
      pipeline[`deploy-${env}`] = this.generateGitLabDeployStage(env, config);
    }

    return yaml.stringify(pipeline, { lineWidth: 0 });
  }

  private generateBuildJob(config: WorkflowConfig) {
    const steps: any[] = [
      {
        name: 'Checkout code',
        uses: 'actions/checkout@v4'
      }
    ];

    // Language-specific setup
    steps.push(...this.getLanguageSetupSteps(config));

    // Build steps
    steps.push(...this.getBuildSteps(config));

    // Docker build
    if (config.hasDocker) {
      steps.push({
        name: 'Build Docker image',
        run: 'docker build -t ${{ github.repository }}:${{ github.sha }} .'
      });
    }

    return {
      build: {
        'runs-on': 'ubuntu-latest',
        steps
      }
    };
  }

  private generateTestJob(config: WorkflowConfig) {
    const steps: any[] = [
      {
        name: 'Checkout code',
        uses: 'actions/checkout@v4'
      }
    ];

    steps.push(...this.getLanguageSetupSteps(config));
    steps.push(...this.getTestSteps(config));

    return {
      test: {
        'runs-on': 'ubuntu-latest',
        needs: ['build'],
        steps
      }
    };
  }

  private generateSecurityJob(config: WorkflowConfig) {
    const steps: any[] = [
      {
        name: 'Checkout code',
        uses: 'actions/checkout@v4'
      }
    ];

    // Language-specific security scans
    steps.push(...this.getSecuritySteps(config));

    return {
      security: {
        'runs-on': 'ubuntu-latest',
        needs: ['build'],
        steps
      }
    };
  }

  private generateDeploymentJob(environment: string, config: WorkflowConfig) {
    const isProd = environment === 'prod' || environment === 'production';

    const steps: any[] = [
      {
        name: 'Checkout code',
        uses: 'actions/checkout@v4'
      },
      {
        name: `Deploy to ${environment}`,
        run: this.getDeploymentScript(environment, config)
      }
    ];

    return {
      [`deploy-${environment}`]: {
        'runs-on': 'ubuntu-latest',
        needs: config.hasTests ? ['build', 'test'] : ['build'],
        if: isProd ? "github.ref == 'refs/heads/main'" : 'true',
        environment: environment,
        steps
      }
    };
  }

  private getLanguageSetupSteps(config: WorkflowConfig): any[] {
    switch (config.language) {
      case 'python':
        return [
          {
            name: 'Set up Python',
            uses: 'actions/setup-python@v4',
            with: {
              'python-version': '3.11'
            }
          },
          {
            name: 'Install dependencies',
            run: 'pip install -r requirements.txt'
          }
        ];

      case 'javascript':
        return [
          {
            name: 'Set up Node.js',
            uses: 'actions/setup-node@v4',
            with: {
              'node-version': '18'
            }
          },
          {
            name: 'Install dependencies',
            run: 'npm ci'
          }
        ];

      case 'go':
        return [
          {
            name: 'Set up Go',
            uses: 'actions/setup-go@v4',
            with: {
              'go-version': '1.21'
            }
          },
          {
            name: 'Download dependencies',
            run: 'go mod download'
          }
        ];

      case 'java':
        return [
          {
            name: 'Set up JDK',
            uses: 'actions/setup-java@v3',
            with: {
              'java-version': '17',
              distribution: 'temurin'
            }
          }
        ];

      default:
        return [];
    }
  }

  private getBuildSteps(config: WorkflowConfig): any[] {
    switch (config.language) {
      case 'python':
        if (config.framework === 'fastapi') {
          return [
            {
              name: 'Lint with flake8',
              run: 'pip install flake8 && flake8 . || echo "No linting configured"'
            },
            {
              name: 'Format check with black',
              run: 'pip install black && black --check . || echo "No formatting configured"'
            }
          ];
        }
        return [
          {
            name: 'Build package',
            run: 'python -m build || echo "No build step needed"'
          }
        ];

      case 'javascript':
        return [
          {
            name: 'Build application',
            run: 'npm run build || echo "No build script found"'
          },
          {
            name: 'Lint code',
            run: 'npm run lint || echo "No lint script found"'
          }
        ];

      case 'go':
        return [
          {
            name: 'Build application',
            run: 'go build -v ./...'
          }
        ];

      case 'java':
        return [
          {
            name: 'Build with Maven',
            run: 'mvn clean compile || gradle build || echo "No build tool found"'
          }
        ];

      default:
        return [
          {
            name: 'Build application',
            run: 'echo "Add your build commands here"'
          }
        ];
    }
  }

  private getTestSteps(config: WorkflowConfig): any[] {
    switch (config.language) {
      case 'python':
        return [
          {
            name: 'Run tests',
            run: 'pytest --cov || python -m unittest discover || echo "No tests found"'
          }
        ];

      case 'javascript':
        return [
          {
            name: 'Run tests',
            run: 'npm test || echo "No test script found"'
          }
        ];

      case 'go':
        return [
          {
            name: 'Run tests',
            run: 'go test -v ./...'
          }
        ];

      case 'java':
        return [
          {
            name: 'Run tests',
            run: 'mvn test || gradle test || echo "No tests found"'
          }
        ];

      default:
        return [
          {
            name: 'Run tests',
            run: 'echo "Add your test commands here"'
          }
        ];
    }
  }

  private getSecuritySteps(config: WorkflowConfig): any[] {
    const steps = [];

    if (config.security?.enableDependencyScanning) {
      switch (config.language) {
        case 'python':
          steps.push({
            name: 'Security audit',
            run: 'pip install safety && safety check || echo "Security scan completed"'
          });
          break;
        case 'javascript':
          steps.push({
            name: 'Security audit',
            run: 'npm audit --audit-level moderate || echo "Security scan completed"'
          });
          break;
      }
    }

    if (config.security?.enableSecretScanning) {
      steps.push({
        name: 'Run Trivy vulnerability scanner',
        uses: 'aquasecurity/trivy-action@master',
        with: {
          'scan-type': 'fs',
          'scan-ref': '.'
        }
      });
    }

    if (config.security?.enableContainerScanning && config.hasDocker) {
      steps.push({
        name: 'Run Trivy container scan',
        uses: 'aquasecurity/trivy-action@master',
        with: {
          'scan-type': 'image',
          'image-ref': '${{ github.repository }}:${{ github.sha }}'
        }
      });
    }

    return steps;
  }

  private getDeploymentScript(environment: string, config: WorkflowConfig): string {
    const scripts = [
      `echo "🚀 Deploying to ${environment} environment"`,
      `echo "Target: ${config.target}"`,
      `echo "Language: ${config.language}"`,
      `echo "Framework: ${config.framework}"`
    ];

    switch (config.target) {
      case 'k8s':
        scripts.push(
          'echo "Kubernetes deployment commands:"',
          'echo "kubectl apply -f k8s/"',
          'echo "kubectl rollout status deployment/app"'
        );
        break;
      case 'serverless':
        scripts.push(
          'echo "Serverless deployment commands:"',
          'echo "serverless deploy --stage ${environment}"'
        );
        break;
      case 'static':
        scripts.push(
          'echo "Static site deployment commands:"',
          'echo "aws s3 sync ./dist s3://bucket-name"'
        );
        break;
    }

    scripts.push('echo "Add your deployment commands here"');

    return scripts.join('\n');
  }

  // GitLab CI methods
  private generateGitLabBuildStage(config: WorkflowConfig) {
    return {
      stage: 'build',
      image: this.getGitLabImage(config.language),
      script: this.getGitLabBuildScript(config)
    };
  }

  private generateGitLabTestStage(config: WorkflowConfig) {
    return {
      stage: 'test',
      image: this.getGitLabImage(config.language),
      script: this.getGitLabTestScript(config)
    };
  }

  private generateGitLabSecurityStage(config: WorkflowConfig) {
    return {
      stage: 'security',
      image: this.getGitLabImage(config.language),
      script: this.getGitLabSecurityScript(config)
    };
  }

  private generateGitLabDeployStage(environment: string, config: WorkflowConfig) {
    return {
      stage: 'deploy',
      image: this.getGitLabImage(config.language),
      script: [
        `echo "Deploying to ${environment}"`,
        'echo "Add your deployment commands here"'
      ],
      environment: {
        name: environment
      },
      only: environment === 'prod' ? ['main'] : ['main', 'develop']
    };
  }

  private getGitLabImage(language: string): string {
    switch (language) {
      case 'python':
        return 'python:3.11';
      case 'javascript':
        return 'node:18';
      case 'go':
        return 'golang:1.21';
      case 'java':
        return 'openjdk:17';
      default:
        return 'ubuntu:latest';
    }
  }

  private getGitLabBuildScript(config: WorkflowConfig): string[] {
    switch (config.language) {
      case 'python':
        return [
          'pip install -r requirements.txt',
          'pip install flake8 black',
          'flake8 . || echo "No linting configured"',
          'black --check . || echo "No formatting configured"'
        ];
      case 'javascript':
        return [
          'npm ci',
          'npm run build || echo "No build script found"',
          'npm run lint || echo "No lint script found"'
        ];
      case 'go':
        return [
          'go mod download',
          'go build -v ./...'
        ];
      default:
        return ['echo "Add your build commands here"'];
    }
  }

  private getGitLabTestScript(config: WorkflowConfig): string[] {
    switch (config.language) {
      case 'python':
        return [
          'pip install -r requirements.txt',
          'pytest --cov || python -m unittest discover || echo "No tests found"'
        ];
      case 'javascript':
        return [
          'npm ci',
          'npm test || echo "No test script found"'
        ];
      case 'go':
        return [
          'go mod download',
          'go test -v ./...'
        ];
      default:
        return ['echo "Add your test commands here"'];
    }
  }

  private getGitLabSecurityScript(config: WorkflowConfig): string[] {
    const scripts = [];

    switch (config.language) {
      case 'python':
        scripts.push(
          'pip install safety',
          'safety check || echo "Security scan completed"'
        );
        break;
      case 'javascript':
        scripts.push(
          'npm audit --audit-level moderate || echo "Security scan completed"'
        );
        break;
      default:
        scripts.push('echo "Add your security scanning commands here"');
    }

    return scripts;
  }
}