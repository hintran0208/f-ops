import fs from 'fs-extra';
import path from 'path';

export interface ProjectAnalysis {
  language: string;
  framework: string;
  packageManager: string;
  hasTests: boolean;
  hasDocker: boolean;
  cloudReady: boolean;
  recommendedTarget: string;
  dependencies: string[];
  buildTools: string[];
  deploymentHints: {
    containerized: boolean;
    hasDockerfile: boolean;
    hasKubernetes: boolean;
    hasServerless: boolean;
  };
}

export class ProjectScanner {
  private projectPath: string;

  constructor(projectPath: string = '.') {
    this.projectPath = path.resolve(projectPath);
  }

  async scanProject(): Promise<ProjectAnalysis> {
    const files = await this.getProjectFiles();

    const analysis: ProjectAnalysis = {
      language: this.detectLanguage(files),
      framework: '',
      packageManager: this.detectPackageManager(files),
      hasTests: this.detectTests(files),
      hasDocker: files.includes('Dockerfile'),
      cloudReady: false,
      recommendedTarget: 'k8s',
      dependencies: [],
      buildTools: [],
      deploymentHints: {
        containerized: files.includes('Dockerfile'),
        hasDockerfile: files.includes('Dockerfile'),
        hasKubernetes: files.some(f => f.includes('k8s') || f.includes('kubernetes')),
        hasServerless: files.some(f => f.includes('serverless') || f.includes('lambda'))
      }
    };

    // Detect framework based on language
    analysis.framework = await this.detectFramework(analysis.language, files);

    // Load dependencies
    analysis.dependencies = await this.getDependencies(analysis.language);

    // Determine cloud readiness
    analysis.cloudReady = analysis.hasDocker || analysis.deploymentHints.hasKubernetes;

    // Recommend target
    analysis.recommendedTarget = this.recommendTarget(analysis);

    // Detect build tools
    analysis.buildTools = this.detectBuildTools(files, analysis.language);

    return analysis;
  }

  private async getProjectFiles(): Promise<string[]> {
    const files: string[] = [];

    try {
      const entries = await fs.readdir(this.projectPath, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.name.startsWith('.') && !['Dockerfile', '.github', '.gitlab'].some(allowed => entry.name.includes(allowed))) {
          continue;
        }

        if (entry.isFile()) {
          files.push(entry.name);
        } else if (entry.isDirectory()) {
          files.push(entry.name + '/');

          // Scan some important subdirectories
          if (['src', 'lib', 'app', 'test', 'tests', '.github', '.gitlab'].includes(entry.name)) {
            try {
              const subFiles = await fs.readdir(path.join(this.projectPath, entry.name));
              files.push(...subFiles.map(f => `${entry.name}/${f}`));
            } catch (error) {
              // Ignore permission errors
            }
          }
        }
      }
    } catch (error) {
      console.error('Error scanning project:', error);
    }

    return files;
  }

  private detectLanguage(files: string[]): string {
    // Python
    if (files.some(f => f.endsWith('.py')) || files.includes('requirements.txt') || files.includes('pyproject.toml')) {
      return 'python';
    }

    // Node.js/JavaScript
    if (files.includes('package.json') || files.some(f => f.endsWith('.js') || f.endsWith('.ts'))) {
      return 'javascript';
    }

    // Go
    if (files.includes('go.mod') || files.some(f => f.endsWith('.go'))) {
      return 'go';
    }

    // Java
    if (files.includes('pom.xml') || files.includes('build.gradle') || files.some(f => f.endsWith('.java'))) {
      return 'java';
    }

    // Rust
    if (files.includes('Cargo.toml') || files.some(f => f.endsWith('.rs'))) {
      return 'rust';
    }

    return 'unknown';
  }

  private async detectFramework(language: string, files: string[]): Promise<string> {
    try {
      switch (language) {
        case 'python':
          return await this.detectPythonFramework();
        case 'javascript':
          return await this.detectJavaScriptFramework();
        case 'go':
          return await this.detectGoFramework();
        case 'java':
          return 'spring';
        default:
          return 'unknown';
      }
    } catch (error) {
      return 'unknown';
    }
  }

  private async detectPythonFramework(): Promise<string> {
    try {
      // Check requirements.txt
      if (await fs.pathExists(path.join(this.projectPath, 'requirements.txt'))) {
        const requirements = await fs.readFile(path.join(this.projectPath, 'requirements.txt'), 'utf-8');
        if (requirements.includes('fastapi')) return 'fastapi';
        if (requirements.includes('django')) return 'django';
        if (requirements.includes('flask')) return 'flask';
      }

      // Check pyproject.toml
      if (await fs.pathExists(path.join(this.projectPath, 'pyproject.toml'))) {
        const pyproject = await fs.readFile(path.join(this.projectPath, 'pyproject.toml'), 'utf-8');
        if (pyproject.includes('fastapi')) return 'fastapi';
        if (pyproject.includes('django')) return 'django';
        if (pyproject.includes('flask')) return 'flask';
      }
    } catch (error) {
      // Ignore file read errors
    }

    return 'unknown';
  }

  private async detectJavaScriptFramework(): Promise<string> {
    try {
      if (await fs.pathExists(path.join(this.projectPath, 'package.json'))) {
        const packageJson = await fs.readJson(path.join(this.projectPath, 'package.json'));
        const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };

        if (deps.express) return 'express';
        if (deps.next) return 'nextjs';
        if (deps.react) return 'react';
        if (deps.vue) return 'vue';
        if (deps.angular) return 'angular';
        if (deps.nestjs) return 'nestjs';
      }
    } catch (error) {
      // Ignore file read errors
    }

    return 'unknown';
  }

  private async detectGoFramework(): Promise<string> {
    try {
      if (await fs.pathExists(path.join(this.projectPath, 'go.mod'))) {
        const goMod = await fs.readFile(path.join(this.projectPath, 'go.mod'), 'utf-8');
        if (goMod.includes('gin-gonic/gin')) return 'gin';
        if (goMod.includes('gorilla/mux')) return 'gorilla';
        if (goMod.includes('fiber')) return 'fiber';
      }
    } catch (error) {
      // Ignore file read errors
    }

    return 'unknown';
  }

  private detectPackageManager(files: string[]): string {
    if (files.includes('package-lock.json')) return 'npm';
    if (files.includes('yarn.lock')) return 'yarn';
    if (files.includes('pnpm-lock.yaml')) return 'pnpm';
    if (files.includes('requirements.txt') || files.includes('pyproject.toml')) return 'pip';
    if (files.includes('go.mod')) return 'go';
    if (files.includes('Cargo.toml')) return 'cargo';
    if (files.includes('pom.xml')) return 'maven';
    if (files.includes('build.gradle')) return 'gradle';

    return 'unknown';
  }

  private detectTests(files: string[]): boolean {
    return files.some(f =>
      f.includes('test') ||
      f.includes('spec') ||
      f.endsWith('.test.js') ||
      f.endsWith('.test.ts') ||
      f.endsWith('.test.py') ||
      f.endsWith('_test.go')
    );
  }

  private async getDependencies(language: string): Promise<string[]> {
    try {
      switch (language) {
        case 'python':
          return await this.getPythonDependencies();
        case 'javascript':
          return await this.getJavaScriptDependencies();
        default:
          return [];
      }
    } catch (error) {
      return [];
    }
  }

  private async getPythonDependencies(): Promise<string[]> {
    const deps: string[] = [];

    try {
      if (await fs.pathExists(path.join(this.projectPath, 'requirements.txt'))) {
        const requirements = await fs.readFile(path.join(this.projectPath, 'requirements.txt'), 'utf-8');
        deps.push(...requirements.split('\n').filter(line => line.trim() && !line.startsWith('#')));
      }
    } catch (error) {
      // Ignore errors
    }

    return deps;
  }

  private async getJavaScriptDependencies(): Promise<string[]> {
    const deps: string[] = [];

    try {
      if (await fs.pathExists(path.join(this.projectPath, 'package.json'))) {
        const packageJson = await fs.readJson(path.join(this.projectPath, 'package.json'));
        const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
        deps.push(...Object.keys(allDeps));
      }
    } catch (error) {
      // Ignore errors
    }

    return deps;
  }

  private recommendTarget(analysis: ProjectAnalysis): string {
    // Static sites
    if (analysis.framework === 'nextjs' || analysis.framework === 'react' || analysis.framework === 'vue') {
      return 'static';
    }

    // Serverless functions
    if (analysis.deploymentHints.hasServerless) {
      return 'serverless';
    }

    // Default to Kubernetes for backend services
    if (analysis.language === 'python' || analysis.language === 'go' || analysis.language === 'java') {
      return 'k8s';
    }

    return 'k8s';
  }

  private detectBuildTools(files: string[], language: string): string[] {
    const tools: string[] = [];

    if (files.includes('Dockerfile')) tools.push('docker');
    if (files.includes('docker-compose.yml')) tools.push('docker-compose');

    switch (language) {
      case 'python':
        tools.push('pip');
        if (files.includes('setup.py')) tools.push('setuptools');
        if (files.includes('pyproject.toml')) tools.push('poetry');
        break;
      case 'javascript':
        if (files.includes('package.json')) tools.push('npm');
        if (files.includes('webpack.config.js')) tools.push('webpack');
        if (files.includes('vite.config.js')) tools.push('vite');
        break;
      case 'go':
        tools.push('go');
        break;
      case 'java':
        if (files.includes('pom.xml')) tools.push('maven');
        if (files.includes('build.gradle')) tools.push('gradle');
        break;
    }

    return tools;
  }
}