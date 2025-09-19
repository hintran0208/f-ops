import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs-extra';
import path from 'path';
import yaml from 'yaml';
import ora from 'ora';
import inquirer from 'inquirer';
import { ProjectScanner } from '../utils/projectScanner';
import { WorkflowGenerator } from '../utils/workflowGenerator';
import { FileOperations } from '../utils/fileOperations';
import { FopsApiClient } from '../services/apiClient';
import { GitUtils } from '../utils/gitUtils';

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
  console.log(chalk.blue.bold('📝 Manual Mode: RAG-Enhanced Guided Configuration'));
  console.log('');

  const apiClient = new FopsApiClient(options.apiUrl);
  const fileOps = new FileOperations('.');

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

  // Scan current project directory
  const projectSpinner = ora('🔍 Scanning current project directory...').start();

  const scanner = new ProjectScanner('.');
  const gitInfo = GitUtils.getGitInfo('.');
  let repoUrl: string;
  let localAnalysis: any;
  let repoInfo: any;

  try {
    // Get local project analysis
    localAnalysis = await scanner.scanProject();
    projectSpinner.succeed('✅ Local project scan completed');

    // Display project information
    console.log(chalk.cyan('\n📁 Current Project Information:'));
    console.log(`  Directory: ${chalk.green(path.basename(process.cwd()))}`);
    console.log(`  Language: ${chalk.green(localAnalysis.language)}`);
    console.log(`  Framework: ${chalk.green(localAnalysis.framework || 'Not detected')}`);
    console.log(`  Git Repository: ${gitInfo.isGitRepo ? '✅ Yes' : '❌ No'}`);

    if (gitInfo.isGitRepo) {
      console.log(`  Remote URL: ${chalk.green(gitInfo.remoteUrl || 'Not configured')}`);
      console.log(`  Current Branch: ${chalk.green(gitInfo.currentBranch || 'Unknown')}`);
      console.log(`  Uncommitted Changes: ${gitInfo.hasUncommittedChanges ? '⚠️ Yes' : '✅ Clean'}`);
    }

    // Get repository information for API (includes local path for local repos)
    repoInfo = GitUtils.getRepositoryInfo('.');
    repoUrl = options.repo || repoInfo.repoUrl;
  } catch (error) {
    projectSpinner.fail('❌ Failed to scan project directory');
    console.error(chalk.red('Error:'), error);
    return;
  }

  // Analyze repository using AI (combining local and remote analysis)
  const analysisSpinner = ora('🧠 Enhancing local analysis with AI for guided recommendations...').start();

  let stackAnalysis;
  try {
    stackAnalysis = await apiClient.analyzeRepositoryStack(repoUrl);
    analysisSpinner.succeed('✅ AI-powered repository analysis completed');

    // Display simplified AI tech stack analysis
    const stack = stackAnalysis.stack;
    console.log(chalk.green.bold('\n🧠 AI Tech Stack Analysis'));
    console.log(`  Language: ${chalk.green(stack.language || localAnalysis.language || 'Unknown')}`);
    console.log(`  Framework: ${chalk.green(stack.framework || localAnalysis.framework || 'None detected')}`);
    console.log(`  Build System: ${chalk.green(stack.build_system || 'Standard')}`);
    console.log(`  Tests: ${stack.has_tests ? '✅' : '❌'} | Docker: ${stack.has_docker ? '✅' : '❌'} | Cloud Ready: ${stack.cloud_ready ? '✅' : '⚠️'}`);
    console.log(`  Recommended Target: ${chalk.yellow(stack.recommended_target || 'k8s')}`);

    // Guided questionnaire with AI-enhanced defaults
    console.log(chalk.yellow.bold('\n📝 AI-Enhanced Guided Configuration'));
    console.log('Note: Defaults are AI-recommended based on local + remote analysis');
    console.log('');
  } catch (error) {
    analysisSpinner.fail('⚠️ AI analysis failed, proceeding with local analysis only');
    console.log(chalk.yellow('Note: Using local project scan results for configuration'));
    stackAnalysis = {
      stack: {
        language: localAnalysis.language,
        framework: localAnalysis.framework,
        recommended_target: 'k8s'
      }
    };
  }

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'projectName',
      message: 'Project name:',
      default: (stackAnalysis.stack as any)?.project_name || path.basename(process.cwd()),
      validate: (input) => input.trim().length > 0 || 'Project name cannot be empty'
    },
    {
      type: 'list',
      name: 'target',
      message: 'Choose deployment target (AI-recommended shown first):',
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
      default: (stackAnalysis.stack as any)?.recommended_target || 'k8s'
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
    }
  ]);

  // Display final configuration for review
  console.log(chalk.green.bold('\n📋 AI-Enhanced Pipeline Configuration'));
  console.log('');
  console.log(chalk.cyan('🏗️  Project Settings'));
  console.log(`  Repository: ${chalk.green(repoUrl)}`);
  console.log(`  Project Name: ${chalk.green(answers.projectName)}`);
  console.log(`  Deployment Target: ${chalk.yellow(answers.target)}`);
  console.log(`  Environments: ${chalk.cyan(answers.environments.join(' → '))}`);
  console.log(`  AI Analysis: ${chalk.green('Enhanced with knowledge base insights')}`);

  if ((stackAnalysis.stack as any)?.language) {
    console.log(chalk.cyan('\n🧠 AI-Detected Stack'));
    console.log(`  Language: ${chalk.green((stackAnalysis.stack as any).language)}`);
    console.log(`  Framework: ${chalk.green((stackAnalysis.stack as any).framework || 'Detected')}`);
    console.log(`  Build System: ${chalk.green((stackAnalysis.stack as any).build_system || 'Configured')}`);
  }

  // Confirm generation
  if (!options.dryRun) {
    console.log('');
    const { proceed } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'proceed',
        message: 'Generate AI-powered CI/CD pipeline with knowledge base insights?',
        default: true
      }
    ]);

    if (!proceed) {
      console.log(chalk.yellow('⚠️  Operation cancelled by user'));
      return;
    }
  }

  // Generate pipeline using RAG-powered AI
  const pipelineSpinner = ora('🧠 Generating AI-powered pipeline with guided configuration...').start();

  try {
    const pipelineRequest: any = {
      repo_url: repoUrl,
      target: answers.target,
      environments: answers.environments
    };

    // Add local path for local repositories
    const currentRepoInfo = GitUtils.getRepositoryInfo('.');
    if (currentRepoInfo.localPath) {
      pipelineRequest.local_path = currentRepoInfo.localPath;
    }

    if (options.dryRun) {
      pipelineSpinner.succeed('✅ AI pipeline generation simulated (dry-run mode)');
      console.log(chalk.blue('\n🔄 [DRY-RUN] Manual mode AI pipeline preview:'));
      console.log(`  📄 Repository: ${repoUrl}`);
      console.log(`  🎯 Target: ${answers.target}`);
      console.log(`  🌍 Environments: ${answers.environments.join(', ')}`);
      console.log('  🧠 Would use RAG knowledge base for guided best practices');
      console.log('  📋 Would create PR with customized CI/CD pipeline');
    } else {
      const pipelineResult = await apiClient.generatePipeline(pipelineRequest);

      pipelineSpinner.succeed('✅ AI-powered guided pipeline generated and PR created!');

      console.log(chalk.green.bold('\n🎉 Guided Pipeline Generation Successful!'));
      console.log('');
      console.log(chalk.cyan('📋 Generation Details:'));
      console.log(`  Configuration: ${chalk.green('Manual guided + AI enhanced')}`);
      console.log(`  Pipeline File: ${chalk.green(pipelineResult.pipeline_file)}`);
      console.log(`  Validation Status: ${chalk.green(pipelineResult.validation_status)}`);
      console.log(`  Pull Request: ${chalk.blue(pipelineResult.pr_url)}`);

      if (pipelineResult.citations && pipelineResult.citations.length > 0) {
        console.log(chalk.cyan('\n📚 Knowledge Base Sources Applied:'));
        pipelineResult.citations.forEach((citation, index) => {
          console.log(`  ${index + 1}. ${chalk.gray(citation)}`);
        });
      }

      console.log(chalk.cyan('\n🔍 Final Stack Configuration:'));
      console.log(`  Language: ${chalk.green(pipelineResult.stack?.language || 'AI-optimized')}`);
      console.log(`  Framework: ${chalk.green(pipelineResult.stack?.framework || 'AI-configured')}`);
      console.log(`  Deployment: ${chalk.green(answers.target)}`);
    }

    // Show next steps
    console.log(chalk.yellow.bold('\n📌 Next Steps:'));
    if (options.dryRun) {
      console.log('  1. 🚀 Run without --dry-run to generate actual pipeline');
      console.log('  2. 🏥 Ensure F-Ops backend is running');
    } else {
      console.log('  1. 📋 Review the generated PR and guided configuration');
      console.log('  2. 🔧 All your manual preferences have been incorporated');
      console.log('  3. ✅ Approve and merge the PR to activate the pipeline');
      console.log('  4. 🔐 Configure required secrets based on your selections');
      console.log('  5. 🚀 Push code changes to trigger the AI-optimized pipeline');
    }

    // Provide target-specific guidance
    if (answers.target === 'k8s') {
      console.log(chalk.blue('\n💡 Kubernetes deployment guidance included in generated PR'));
    } else if (answers.target === 'serverless') {
      console.log(chalk.blue('\n💡 Serverless deployment patterns included in generated PR'));
    } else if (answers.target === 'static') {
      console.log(chalk.blue('\n💡 Static site deployment configuration included in generated PR'));
    }

    console.log(chalk.green.bold('\n🎉 RAG-enhanced manual mode completed successfully!'));

  } catch (error) {
    pipelineSpinner.fail('❌ Failed to generate AI-powered guided pipeline');
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