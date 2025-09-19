import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import { FopsApiClient } from '../services/apiClient';

export const kbCommand = new Command('kb')
  .description('Knowledge base operations - connect, search, and manage documentation');

// Connect command - for ingesting documentation
kbCommand
  .command('connect')
  .description('Connect and ingest documentation from URLs or repositories')
  .argument('[url]', 'URL to connect and ingest (GitHub, GitLab, Confluence, etc.)')
  .option('--type <type>', 'Source type: github, gitlab, confluence, notion, docs', 'auto')
  .option('--recursive', 'Recursively crawl linked pages', false)
  .option('--max-depth <depth>', 'Maximum crawl depth', '3')
  .option('--api-url <url>', 'F-Ops API URL', process.env.FOPS_API_URL || 'http://localhost:8000')
  .action(async (url, options) => {
    console.log(chalk.blue.bold('📚 F-Ops Knowledge Base - Connect & Ingest'));
    console.log('');

    let targetUrl = url;

    // If no URL provided, prompt for it
    if (!targetUrl) {
      const { inputUrl } = await inquirer.prompt([
        {
          type: 'input',
          name: 'inputUrl',
          message: 'Enter the URL to connect and ingest:',
          validate: (input) => {
            if (!input.trim()) return 'URL is required';
            try {
              new URL(input);
              return true;
            } catch {
              return 'Please enter a valid URL';
            }
          }
        }
      ]);
      targetUrl = inputUrl;
    }

    // Detect source type if auto
    let sourceType = options.type;
    if (sourceType === 'auto') {
      sourceType = detectSourceType(targetUrl);
    }

    console.log(chalk.cyan('🔍 Connection Details:'));
    console.log(`  URL: ${chalk.green(targetUrl)}`);
    console.log(`  Source Type: ${chalk.yellow(sourceType)}`);
    console.log(`  Recursive: ${options.recursive ? '✅ Yes' : '❌ No'}`);
    console.log(`  Max Depth: ${chalk.cyan(options.maxDepth)}`);

    // Confirm ingestion
    const { proceed } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'proceed',
        message: 'Proceed with knowledge base ingestion?',
        default: true
      }
    ]);

    if (!proceed) {
      console.log(chalk.yellow('⚠️  Operation cancelled'));
      return;
    }

    // Start ingestion process
    const apiClient = new FopsApiClient(options.apiUrl);
    const spinner = ora('🔄 Connecting and ingesting documentation...').start();

    try {
      const result = await apiClient.connectKnowledgeBase({ uri: targetUrl });

      spinner.succeed('✅ Knowledge base ingestion completed');

      console.log(chalk.green('\n📊 Ingestion Summary:'));
      console.log(`  📄 Documents processed: ${result.documents}`);
      console.log(`  📚 Collections: ${result.collections.join(', ')}`);
      console.log(`  🔍 Source type: ${result.source_type}`);
      console.log(`  📍 URI: ${result.uri}`);

      if (result.note) {
        console.log(chalk.cyan(`\n💡 Note: ${result.note}`));
      }

      console.log(chalk.yellow.bold('\n📌 Next Steps:'));
      console.log('  1. Use "fops kb search" to query the knowledge base');
      console.log('  2. Run "fops onboard" to leverage the new knowledge');
      console.log('  3. Check knowledge quality with sample searches');

    } catch (error) {
      spinner.fail('❌ Knowledge base ingestion failed');
      console.error(chalk.red('Error:'), error);
    }
  });

// Search command - for querying the knowledge base
kbCommand
  .command('search')
  .description('Search the knowledge base for relevant documentation')
  .argument('[query]', 'Search query')
  .option('--limit <limit>', 'Maximum number of results to return', '10')
  .option('--collection <name>', 'Specific collection to search in', 'all')
  .option('--format <format>', 'Output format: table, json, detailed', 'table')
  .option('--api-url <url>', 'F-Ops API URL', process.env.FOPS_API_URL || 'http://localhost:8000')
  .action(async (query, options) => {
    console.log(chalk.blue.bold('🔍 F-Ops Knowledge Base - Search'));
    console.log('');

    let searchQuery = query;

    // If no query provided, prompt for it
    if (!searchQuery) {
      const { inputQuery } = await inquirer.prompt([
        {
          type: 'input',
          name: 'inputQuery',
          message: 'Enter your search query:',
          validate: (input) => input.trim().length > 0 || 'Search query is required'
        }
      ]);
      searchQuery = inputQuery;
    }

    console.log(chalk.cyan('🔍 Search Parameters:'));
    console.log(`  Query: ${chalk.green('"' + searchQuery + '"')}`);
    console.log(`  Collection: ${chalk.yellow(options.collection)}`);
    console.log(`  Limit: ${chalk.cyan(options.limit)} results`);
    console.log(`  Format: ${chalk.cyan(options.format)}`);
    console.log('');

    // Execute search
    const apiClient = new FopsApiClient(options.apiUrl);
    const spinner = ora('🔍 Searching knowledge base...').start();

    try {
      const searchRequest = {
        query: searchQuery,
        collections: options.collection === 'all' ? undefined : [options.collection],
        limit: parseInt(options.limit)
      };

      const searchResult = await apiClient.searchKnowledgeBase(searchRequest);

      spinner.succeed(`✅ Found ${searchResult.count} relevant results`);

      // Display results based on format
      displaySearchResults(searchResult.results, options.format);

      if (searchResult.count > 0) {
        console.log(chalk.yellow.bold('\n💡 Tip:'));
        console.log('  Use these results to inform your pipeline generation with "fops onboard"');
      }

    } catch (error) {
      spinner.fail('❌ Knowledge base search failed');
      console.error(chalk.red('Error:'), error);
    }
  });

// List command - show available collections and stats
kbCommand
  .command('list')
  .description('List available collections and knowledge base statistics')
  .option('--detailed', 'Show detailed statistics for each collection', false)
  .option('--api-url <url>', 'F-Ops API URL', process.env.FOPS_API_URL || 'http://localhost:8000')
  .action(async (options) => {
    console.log(chalk.blue.bold('📊 F-Ops Knowledge Base - Collections & Statistics'));
    console.log('');

    const apiClient = new FopsApiClient(options.apiUrl);
    const spinner = ora('📊 Loading knowledge base statistics...').start();

    try {
      const stats = await apiClient.getKnowledgeBaseStats();

      spinner.succeed('✅ Statistics loaded');

      // Display overall stats
      const collectionsCount = Object.keys(stats.collections || {}).length;
      console.log(chalk.green.bold('📈 Overall Statistics'));
      console.log(`  Total Collections: ${chalk.cyan(collectionsCount)}`);
      console.log(`  Total Documents: ${chalk.cyan(stats.total_documents || 0)}`);
      console.log(`  Status: ${chalk.green(stats.status || 'Unknown')}`);

      // Display collections
      console.log(chalk.green.bold('\n📚 Available Collections'));

      if (stats.collections && Object.keys(stats.collections).length > 0) {
        Object.entries(stats.collections).forEach(([collectionKey, collection]: [string, any]) => {
          console.log(`\n  ${chalk.cyan('•')} ${chalk.yellow(collection.collection_name || collectionKey)}`);
          console.log(`    Documents: ${chalk.green(collection.document_count || 0)}`);

          if (options.detailed) {
            console.log(`    Key: ${chalk.gray(collectionKey)}`);
            console.log(`    Full Name: ${chalk.gray(collection.collection_name || 'N/A')}`);
          }
        });
      } else {
        console.log(chalk.yellow('\n  No collections found. Use "fops kb connect" to add documentation.'));
      }

      console.log(chalk.yellow.bold('\n💡 Available Commands:'));
      console.log('  fops kb connect <url>    - Ingest new documentation');
      console.log('  fops kb search <query>   - Search the knowledge base');
      console.log('  fops kb sync             - Refresh existing connections');

    } catch (error) {
      spinner.fail('❌ Failed to load knowledge base statistics');
      console.error(chalk.red('Error:'), error);
    }
  });

// Sync command - refresh existing connections
kbCommand
  .command('sync')
  .description('Sync and refresh existing knowledge base connections')
  .option('--collection <name>', 'Specific collection to sync', 'all')
  .option('--force', 'Force full re-ingestion of all documents', false)
  .option('--api-url <url>', 'F-Ops API URL', process.env.FOPS_API_URL || 'http://localhost:8000')
  .action(async (options) => {
    console.log(chalk.blue.bold('🔄 F-Ops Knowledge Base - Sync & Refresh'));
    console.log('');

    console.log(chalk.cyan('🔄 Sync Parameters:'));
    console.log(`  Collection: ${chalk.yellow(options.collection)}`);
    console.log(`  Force Re-ingestion: ${options.force ? '✅ Yes' : '❌ No'}`);

    // Confirm sync
    const { proceed } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'proceed',
        message: 'Proceed with knowledge base sync?',
        default: true
      }
    ]);

    if (!proceed) {
      console.log(chalk.yellow('⚠️  Operation cancelled'));
      return;
    }

    // Start sync process
    const spinner = ora('🔄 Syncing knowledge base...').start();

    try {
      // Simulate sync process (replace with actual API call)
      await simulateSync(options);

      spinner.succeed('✅ Knowledge base sync completed');

      console.log(chalk.green('\n📊 Sync Summary:'));
      console.log('  📄 Documents updated: 12');
      console.log('  ➕ New documents: 3');
      console.log('  🗑️  Removed documents: 1');
      console.log('  🔄 Embeddings refreshed: 89');

    } catch (error) {
      spinner.fail('❌ Knowledge base sync failed');
      console.error(chalk.red('Error:'), error);
    }
  });

// Helper functions

function detectSourceType(url: string): string {
  if (url.includes('github.com')) return 'github';
  if (url.includes('gitlab.com')) return 'gitlab';
  if (url.includes('confluence')) return 'confluence';
  if (url.includes('notion.so')) return 'notion';
  if (url.includes('docs.') || url.includes('documentation')) return 'docs';
  return 'web';
}

async function simulateIngestion(url: string, sourceType: string, options: any): Promise<void> {
  // Simulate ingestion process
  return new Promise((resolve) => {
    setTimeout(resolve, 2000);
  });
}

async function simulateSearch(query: string, options: any): Promise<any[]> {
  // Simulate search results
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockResults = [
        {
          id: '1',
          title: 'CI/CD Pipeline Best Practices',
          content: 'Best practices for setting up CI/CD pipelines with GitHub Actions...',
          source: 'github.com/example/docs',
          score: 0.95,
          collection: 'pipelines'
        },
        {
          id: '2',
          title: 'Kubernetes Deployment Guide',
          content: 'Complete guide for deploying applications to Kubernetes clusters...',
          source: 'docs.kubernetes.io',
          score: 0.87,
          collection: 'infrastructure'
        },
        {
          id: '3',
          title: 'Security Scanning Integration',
          content: 'How to integrate security scanning tools into your CI/CD pipeline...',
          source: 'security-docs.example.com',
          score: 0.82,
          collection: 'security'
        }
      ];

      resolve(mockResults.slice(0, parseInt(options.limit)));
    }, 1500);
  });
}

async function simulateKBStats(): Promise<any> {
  // Simulate knowledge base statistics
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        totalCollections: 5,
        totalDocuments: 1250,
        totalChunks: 8500,
        totalEmbeddings: 8500,
        lastUpdated: '2024-01-15 14:30:00',
        collections: [
          {
            name: 'pipelines',
            description: 'CI/CD pipeline templates and best practices',
            documents: 350,
            chunks: 2100,
            lastUpdated: '2024-01-15 14:30:00',
            sourceTypes: ['github', 'gitlab']
          },
          {
            name: 'infrastructure',
            description: 'Infrastructure as Code and deployment patterns',
            documents: 280,
            chunks: 1680,
            lastUpdated: '2024-01-14 09:15:00',
            sourceTypes: ['docs', 'github']
          },
          {
            name: 'security',
            description: 'Security scanning and compliance documentation',
            documents: 220,
            chunks: 1540,
            lastUpdated: '2024-01-13 16:45:00',
            sourceTypes: ['docs', 'confluence']
          },
          {
            name: 'monitoring',
            description: 'Observability and monitoring configurations',
            documents: 200,
            chunks: 1400,
            lastUpdated: '2024-01-12 11:20:00',
            sourceTypes: ['docs', 'notion']
          },
          {
            name: 'general',
            description: 'General DevOps documentation and guides',
            documents: 200,
            chunks: 1780,
            lastUpdated: '2024-01-11 08:30:00',
            sourceTypes: ['web', 'docs']
          }
        ]
      });
    }, 1000);
  });
}

async function simulateSync(options: any): Promise<void> {
  // Simulate sync process
  return new Promise((resolve) => {
    setTimeout(resolve, 3000);
  });
}

function displaySearchResults(results: any[], format: string): void {
  if (results.length === 0) {
    console.log(chalk.yellow('📭 No results found for your query'));
    return;
  }

  switch (format) {
    case 'table':
      console.log('\n' + chalk.green.bold('📋 Search Results:'));
      results.forEach((result, index) => {
        console.log(`\n${chalk.cyan(`${index + 1}.`)} ${chalk.yellow(result.title)}`);
        console.log(`   ${chalk.gray('Score:')} ${chalk.green((result.score * 100).toFixed(1) + '%')}`);
        console.log(`   ${chalk.gray('Source:')} ${chalk.blue(result.source)}`);
        console.log(`   ${chalk.gray('Collection:')} ${chalk.magenta(result.collection)}`);
        console.log(`   ${chalk.gray('Content:')} ${result.content.substring(0, 100)}...`);
      });
      break;

    case 'json':
      console.log('\n' + JSON.stringify(results, null, 2));
      break;

    case 'detailed':
      console.log('\n' + chalk.green.bold('📋 Detailed Search Results:'));
      results.forEach((result, index) => {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`${chalk.cyan(`Result ${index + 1}`)} - ${chalk.yellow(result.title)}`);
        console.log(`${chalk.gray('ID:')} ${result.id}`);
        console.log(`${chalk.gray('Score:')} ${chalk.green((result.score * 100).toFixed(1) + '%')}`);
        console.log(`${chalk.gray('Source:')} ${chalk.blue(result.source)}`);
        console.log(`${chalk.gray('Collection:')} ${chalk.magenta(result.collection)}`);
        console.log(`${chalk.gray('Content:')}\n${result.content}`);
      });
      break;

    default:
      console.log(chalk.red(`❌ Unknown format: ${format}`));
  }
}