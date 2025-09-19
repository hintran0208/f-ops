import { Command } from 'commander';
import chalk from 'chalk';
import path from 'path';
import ora from 'ora';
import inquirer from 'inquirer';
import { FopsApiClient } from '../services/apiClient';

export const onboardCommand = new Command('onboard')
  .description('Repository onboarding - guides you through auto/manual mode selection')
  .option('--dry-run', 'Show what would be created without making changes', false)
  .option('--repo <url>', 'Repository URL (optional)')
  .option('--api-url <url>', 'F-Ops API URL', process.env.FOPS_API_URL || 'http://localhost:8000')
  .action(async (options) => {
    console.log(chalk.blue.bold('🚀 Welcome to F-Ops Repository Onboarding'));
    console.log('');

    // First, guide user to choose between auto and manual modes
    const { mode } = await inquirer.prompt([
      {
        type: 'list',
        name: 'mode',
        message: 'Choose your onboarding mode:',
        choices: [
          {
            name: '🤖 Auto Mode - Automatically scan project and generate pipeline',
            value: 'auto',
            short: 'Auto'
          },
          {
            name: '📝 Manual Mode - Guided questionnaire for custom configuration',
            value: 'manual',
            short: 'Manual'
          }
        ]
      }
    ]);

    if (mode === 'auto') {
      await runAutoMode(options);
    } else {
      await runManualMode(options);
    }
  });

async function runAutoMode(options: any) {
  console.log(chalk.blue.bold('🤖 Auto Mode: AI-Powered Pipeline Generation'));
  console.log('');

  const apiClient = new FopsApiClient(options.apiUrl);

  // Quick backend health check
  const healthSpinner = ora('Connecting to F-Ops backend...').start();
  try {
    const isHealthy = await apiClient.checkHealth();
    if (!isHealthy) {
      healthSpinner.fail('❌ F-Ops backend is not responding');
      console.log(chalk.yellow('💡 Please start the backend: cd backend && python -m uvicorn app.main:app --reload --port 8000'));
      return;
    }
    healthSpinner.succeed('✅ Connected to F-Ops backend');
  } catch (error) {
    healthSpinner.fail('❌ Failed to connect to F-Ops backend');
    return;
  }

  // Step 1: Comprehensive AI Analysis
  const analysisSpinner = ora('🧠 AI analyzing your codebase...').start();

  try {
    // Use comprehensive analysis API
    const comprehensiveAnalysis = await apiClient.comprehensiveAnalysis({
      local_path: process.cwd()
    });

    analysisSpinner.succeed('✅ AI analysis completed');

    // Display clean AI tech stack analysis
    console.log(chalk.green.bold('\n🧠 AI Tech Stack Analysis'));
    console.log(`  Language: ${chalk.green(comprehensiveAnalysis.languages_detected?.[0] || 'Unknown')}`);
    console.log(`  Framework: ${chalk.green(comprehensiveAnalysis.frameworks_detected?.[0] || 'None detected')}`);
    console.log(`  Quality Score: ${chalk.yellow(comprehensiveAnalysis.quality_score || 'N/A')}/100`);
    console.log(`  Complexity: ${chalk.cyan(comprehensiveAnalysis.complexity_assessment || 'Unknown')}`);

    // Step 2: Intelligent Pipeline Generation
    const pipelineSpinner = ora('🚀 Generating AI-powered pipeline...').start();

    try {
      const intelligentRequest = {
        local_path: process.cwd(),
        use_analysis: true // Always use comprehensive analysis in auto mode
      };

      const pipelineResult = await apiClient.generateIntelligentPipeline(intelligentRequest);
      pipelineSpinner.succeed('✅ Pipeline generated successfully');

      // Simple success message
      console.log(chalk.green.bold('\n🎉 Auto-mode completed successfully!'));
      console.log(chalk.cyan(`📄 Pipeline file: ${pipelineResult.pipeline_file}`));
      console.log(chalk.yellow('🚀 Pipeline is ready for deployment!'));

    } catch (error) {
      pipelineSpinner.fail('❌ Failed to generate AI-powered pipeline');
      console.error(chalk.red('Error:'), error);
      throw error;
    }

  } catch (error) {
    analysisSpinner.fail('❌ AI repository analysis failed');
    console.error(chalk.red('Error during AI analysis:'), error);
    throw error;
  }
}

async function runManualMode(options: any) {
  console.log(chalk.blue.bold('📝 Manual Mode: Guided Pipeline Configuration'));
  console.log('');

  const apiClient = new FopsApiClient(options.apiUrl);

  // Check backend health first
  const healthSpinner = ora('🏥 Checking F-Ops backend connection...').start();

  try {
    const isHealthy = await apiClient.checkHealth();
    if (!isHealthy) {
      healthSpinner.fail('❌ F-Ops backend is not responding');
      console.log(chalk.yellow('💡 Please ensure the backend is running:'));
      console.log(chalk.cyan('   cd backend && python -m uvicorn app.main:app --reload --port 8000'));
      return;
    }
    healthSpinner.succeed('✅ Backend connection established');
  } catch (error) {
    healthSpinner.fail('❌ Failed to connect to F-Ops backend');
    console.error(chalk.red('Error:'), error);
    return;
  }

  // Simple project info display
  console.log(chalk.cyan('\n📁 Current Project Information:'));
  console.log(`  Directory: ${chalk.green(path.basename(process.cwd()))}`);
  console.log(`  Path: ${chalk.gray(process.cwd())}`);

  // Guided questionnaire for deployment configuration
  console.log(chalk.yellow.bold('\n📝 Deployment Configuration'));
  console.log('Please answer the following questions to configure your CI/CD pipeline:');
  console.log('');

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'projectName',
      message: 'Project name:',
      default: path.basename(process.cwd()),
      validate: (input) => input.trim().length > 0 || 'Project name cannot be empty'
    },
    {
      type: 'list',
      name: 'cloudProvider',
      message: 'Choose cloud provider:',
      choices: [
        {
          name: '☁️  AWS - Amazon Web Services',
          value: 'aws',
          short: 'AWS'
        },
        {
          name: '🌐 Azure - Microsoft Azure',
          value: 'azure',
          short: 'Azure'
        },
        {
          name: '🔴 GCP - Google Cloud Platform',
          value: 'gcp',
          short: 'GCP'
        }
      ],
      default: 'aws'
    },
    {
      type: 'list',
      name: 'target',
      message: 'Choose deployment target:',
      choices: [
        {
          name: '☸️  Kubernetes (k8s) - Container orchestration platform',
          value: 'k8s',
          short: 'Kubernetes'
        },
        {
          name: '⚡ Serverless - Functions as a Service (FaaS)',
          value: 'serverless',
          short: 'Serverless'
        },
        {
          name: '📄 Static - Static site hosting (CDN)',
          value: 'static',
          short: 'Static'
        }
      ],
      default: 'k8s'
    },
    {
      type: 'checkbox',
      name: 'environments',
      message: 'Select target environments:',
      choices: [
        { name: 'development (dev)', value: 'dev', checked: false },
        { name: 'staging', value: 'staging', checked: true },
        { name: 'production (prod)', value: 'prod', checked: true },
        { name: 'testing (test)', value: 'test', checked: false }
      ],
      validate: (input) => input.length > 0 || 'Please select at least one environment'
    },
    {
      type: 'confirm',
      name: 'includeTests',
      message: 'Include automated testing in pipeline?',
      default: true
    },
    {
      type: 'confirm',
      name: 'includeSecurity',
      message: 'Include security scanning?',
      default: true
    },
    {
      type: 'list',
      name: 'buildTool',
      message: 'Preferred build tool/approach:',
      choices: [
        { name: 'Docker - Containerized builds', value: 'docker' },
        { name: 'Native - Use language-specific tools', value: 'native' },
        { name: 'Auto-detect - Let AI choose best approach', value: 'auto' }
      ],
      default: 'auto'
    }
  ]);

  // Display final configuration for review
  console.log(chalk.green.bold('\n📋 Manual Pipeline Configuration'));
  console.log('');
  console.log(chalk.cyan('🏗️  Project Settings'));
  console.log(`  Project Name: ${chalk.green(answers.projectName)}`);
  console.log(`  Cloud Provider: ${chalk.blue(answers.cloudProvider.toUpperCase())}`);
  console.log(`  Deployment Target: ${chalk.yellow(answers.target)}`);
  console.log(`  Environments: ${chalk.cyan(answers.environments.join(' → '))}`);
  console.log(`  Testing: ${answers.includeTests ? '✅ Enabled' : '❌ Disabled'}`);
  console.log(`  Security Scanning: ${answers.includeSecurity ? '✅ Enabled' : '❌ Disabled'}`);
  console.log(`  Build Approach: ${chalk.green(answers.buildTool)}`);

  // Confirm generation
  if (!options.dryRun) {
    console.log('');
    const { proceed } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'proceed',
        message: 'Generate CI/CD pipeline with these settings?',
        default: true
      }
    ]);

    if (!proceed) {
      console.log(chalk.yellow('⚠️  Operation cancelled by user'));
      return;
    }
  }

  // Generate pipeline using manual configuration (no AI analysis)
  const pipelineSpinner = ora('🔧 Generating pipeline with your configuration...').start();

  try {
    const intelligentRequest = {
      local_path: process.cwd(),
      cloud_provider: answers.cloudProvider,
      target: answers.target,
      environments: answers.environments,
      use_analysis: false  // Manual mode doesn't use AI analysis
    };

    if (options.dryRun) {
      pipelineSpinner.succeed('✅ Pipeline generation simulated (dry-run mode)');
      console.log(chalk.blue('\n🔄 [DRY-RUN] Manual mode pipeline preview:'));
      console.log(`  📄 Directory: ${process.cwd()}`);
      console.log(`  ☁️  Cloud Provider: ${answers.cloudProvider.toUpperCase()}`);
      console.log(`  🎯 Target: ${answers.target}`);
      console.log(`  🌍 Environments: ${answers.environments.join(', ')}`);
      console.log(`  🧪 Testing: ${answers.includeTests ? 'Enabled' : 'Disabled'}`);
      console.log(`  🔒 Security: ${answers.includeSecurity ? 'Enabled' : 'Disabled'}`);
      console.log(`  🔧 Build: ${answers.buildTool}`);
      console.log('  📋 Would create pipeline file based on your preferences');
    } else {
      const pipelineResult = await apiClient.generateIntelligentPipeline(intelligentRequest);

      pipelineSpinner.succeed('✅ Manual pipeline generated and file created!');

      console.log(chalk.green.bold('\n🎉 Manual Pipeline Generation Successful!'));
      console.log('');
      console.log(chalk.cyan('📋 Generation Details:'));
      console.log(`  Configuration: ${chalk.green('Manual guided configuration')}`);
      console.log(`  Pipeline File: ${chalk.green(pipelineResult.pipeline_file)}`);
      console.log(`  Validation Status: ${chalk.green(pipelineResult.validation_status)}`);
      console.log(`  File Location: ${chalk.cyan('.github/workflows/' + pipelineResult.pipeline_file)}`);

      if (pipelineResult.rag_sources && pipelineResult.rag_sources.length > 0) {
        console.log(chalk.cyan('\n📚 Knowledge Base Sources Used:'));
        pipelineResult.rag_sources.forEach((source, index) => {
          console.log(`  ${index + 1}. ${chalk.gray(source)}`);
        });
      }

      console.log(chalk.cyan('\n🔍 Pipeline Configuration Applied:'));
      console.log(`  Cloud Provider: ${chalk.blue(answers.cloudProvider.toUpperCase())}`);
      console.log(`  Deployment Target: ${chalk.green(answers.target)}`);
      console.log(`  Environments: ${chalk.green(answers.environments.join(', '))}`);
      console.log(`  Testing: ${answers.includeTests ? '✅ Included' : '❌ Skipped'}`);
      console.log(`  Security: ${answers.includeSecurity ? '✅ Included' : '❌ Skipped'}`);
    }

    // Show next steps
    console.log(chalk.yellow.bold('\n📌 Next Steps:'));
    if (options.dryRun) {
      console.log('  1. 🚀 Run without --dry-run to generate actual pipeline');
      console.log('  2. 🏥 Ensure F-Ops backend is running');
    } else {
      console.log('  1. 📋 Review the generated pipeline file in .github/workflows/');
      console.log('  2. 🔧 Your manual preferences have been applied');
      console.log('  3. ✅ Commit and push the file to activate the pipeline');
      console.log('  4. 🔐 Configure required secrets based on your selections');
    }

    // Provide target-specific guidance
    if (answers.target === 'k8s') {
      console.log(chalk.blue('\n💡 Kubernetes deployment configuration included'));
    } else if (answers.target === 'serverless') {
      console.log(chalk.blue('\n💡 Serverless deployment patterns included'));
    } else if (answers.target === 'static') {
      console.log(chalk.blue('\n💡 Static site deployment configuration included'));
    }

    console.log(chalk.green.bold('\n🎉 Manual mode completed successfully!'));

  } catch (error) {
    pipelineSpinner.fail('❌ Failed to generate manual pipeline');
    console.error(chalk.red('Error:'), error);
    throw error;
  }
}

// Auto Mode: Backend AI handles all decision-making
// The CLI simply passes the repository URL and lets the backend AI:
// 1. Analyze the codebase using the stack analysis
// 2. Make deployment target decisions (static/serverless/k8s)
// 3. Select appropriate environments (dev/staging/prod)
// 4. Generate optimized CI/CD pipeline using RAG knowledge