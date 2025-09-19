import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';

export interface FileModification {
  action: 'create' | 'update' | 'delete' | 'modify';
  filePath: string;
  content?: string;
  modifications?: Array<{
    search: string;
    replace: string;
  }>;
}

export class FileOperations {
  private basePath: string;

  constructor(basePath: string = '.') {
    this.basePath = path.resolve(basePath);
  }

  /**
   * Read file content
   */
  async readFile(filePath: string): Promise<string> {
    try {
      const fullPath = path.resolve(this.basePath, filePath);
      const content = await fs.readFile(fullPath, 'utf-8');
      console.log(chalk.blue(`📖 Read: ${filePath}`));
      return content;
    } catch (error) {
      throw new Error(`Failed to read file ${filePath}: ${(error as Error).message}`);
    }
  }

  /**
   * Write file content (create or overwrite)
   */
  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      const fullPath = path.resolve(this.basePath, filePath);

      // Ensure directory exists
      await fs.ensureDir(path.dirname(fullPath));

      await fs.writeFile(fullPath, content, 'utf-8');
      console.log(chalk.green(`✅ Created: ${filePath}`));
    } catch (error) {
      throw new Error(`Failed to write file ${filePath}: ${(error as Error).message}`);
    }
  }

  /**
   * Delete file
   */
  async deleteFile(filePath: string): Promise<void> {
    try {
      const fullPath = path.resolve(this.basePath, filePath);

      if (await fs.pathExists(fullPath)) {
        await fs.remove(fullPath);
        console.log(chalk.red(`🗑️  Deleted: ${filePath}`));
      } else {
        console.log(chalk.yellow(`⚠️  File not found: ${filePath}`));
      }
    } catch (error) {
      throw new Error(`Failed to delete file ${filePath}: ${(error as Error).message}`);
    }
  }

  /**
   * Modify file content using search and replace
   */
  async modifyFile(filePath: string, modifications: Array<{ search: string; replace: string }>): Promise<void> {
    try {
      const fullPath = path.resolve(this.basePath, filePath);

      if (!await fs.pathExists(fullPath)) {
        throw new Error(`File does not exist: ${filePath}`);
      }

      let content = await fs.readFile(fullPath, 'utf-8');

      for (const mod of modifications) {
        content = content.replace(new RegExp(mod.search, 'g'), mod.replace);
      }

      await fs.writeFile(fullPath, content, 'utf-8');
      console.log(chalk.blue(`🔧 Modified: ${filePath} (${modifications.length} changes)`));
    } catch (error) {
      throw new Error(`Failed to modify file ${filePath}: ${(error as Error).message}`);
    }
  }

  /**
   * Check if file exists
   */
  async fileExists(filePath: string): Promise<boolean> {
    const fullPath = path.resolve(this.basePath, filePath);
    return await fs.pathExists(fullPath);
  }

  /**
   * Create directory
   */
  async createDirectory(dirPath: string): Promise<void> {
    try {
      const fullPath = path.resolve(this.basePath, dirPath);
      await fs.ensureDir(fullPath);
      console.log(chalk.green(`📁 Created directory: ${dirPath}`));
    } catch (error) {
      throw new Error(`Failed to create directory ${dirPath}: ${(error as Error).message}`);
    }
  }

  /**
   * List files in directory
   */
  async listFiles(dirPath: string = '.', recursive: boolean = false): Promise<string[]> {
    try {
      const fullPath = path.resolve(this.basePath, dirPath);

      if (recursive) {
        return await this.listFilesRecursive(fullPath);
      } else {
        const entries = await fs.readdir(fullPath);
        return entries.filter(async (entry) => {
          const entryPath = path.join(fullPath, entry);
          const stat = await fs.stat(entryPath);
          return stat.isFile();
        });
      }
    } catch (error) {
      throw new Error(`Failed to list files in ${dirPath}: ${(error as Error).message}`);
    }
  }

  private async listFilesRecursive(dirPath: string): Promise<string[]> {
    const files: string[] = [];

    const entries = await fs.readdir(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isFile()) {
        files.push(path.relative(this.basePath, fullPath));
      } else if (entry.isDirectory() && !entry.name.startsWith('.')) {
        const subFiles = await this.listFilesRecursive(fullPath);
        files.push(...subFiles);
      }
    }

    return files;
  }

  /**
   * Apply multiple file modifications
   */
  async applyModifications(modifications: FileModification[]): Promise<void> {
    console.log(chalk.blue(`🔄 Applying ${modifications.length} file modifications...`));

    for (const mod of modifications) {
      try {
        switch (mod.action) {
          case 'create':
            if (mod.content === undefined) {
              throw new Error('Content is required for create action');
            }
            await this.writeFile(mod.filePath, mod.content);
            break;

          case 'update':
            if (mod.content === undefined) {
              throw new Error('Content is required for update action');
            }
            await this.writeFile(mod.filePath, mod.content);
            break;

          case 'delete':
            await this.deleteFile(mod.filePath);
            break;

          case 'modify':
            if (!mod.modifications || mod.modifications.length === 0) {
              throw new Error('Modifications are required for modify action');
            }
            await this.modifyFile(mod.filePath, mod.modifications);
            break;

          default:
            throw new Error(`Unknown action: ${(mod as any).action}`);
        }
      } catch (error) {
        console.error(chalk.red(`❌ Failed to apply modification for ${mod.filePath}:`), error);
        throw error;
      }
    }

    console.log(chalk.green('✅ All file modifications applied successfully'));
  }

  /**
   * Copy file
   */
  async copyFile(sourcePath: string, destPath: string): Promise<void> {
    try {
      const fullSourcePath = path.resolve(this.basePath, sourcePath);
      const fullDestPath = path.resolve(this.basePath, destPath);

      await fs.ensureDir(path.dirname(fullDestPath));
      await fs.copy(fullSourcePath, fullDestPath);

      console.log(chalk.green(`📋 Copied: ${sourcePath} → ${destPath}`));
    } catch (error) {
      throw new Error(`Failed to copy file ${sourcePath} to ${destPath}: ${(error as Error).message}`);
    }
  }

  /**
   * Move/rename file
   */
  async moveFile(sourcePath: string, destPath: string): Promise<void> {
    try {
      const fullSourcePath = path.resolve(this.basePath, sourcePath);
      const fullDestPath = path.resolve(this.basePath, destPath);

      await fs.ensureDir(path.dirname(fullDestPath));
      await fs.move(fullSourcePath, fullDestPath);

      console.log(chalk.green(`📁 Moved: ${sourcePath} → ${destPath}`));
    } catch (error) {
      throw new Error(`Failed to move file ${sourcePath} to ${destPath}: ${(error as Error).message}`);
    }
  }

  /**
   * Get file stats
   */
  async getFileStats(filePath: string) {
    try {
      const fullPath = path.resolve(this.basePath, filePath);
      const stats = await fs.stat(fullPath);

      return {
        size: stats.size,
        created: stats.birthtime,
        modified: stats.mtime,
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory()
      };
    } catch (error) {
      throw new Error(`Failed to get stats for ${filePath}: ${(error as Error).message}`);
    }
  }

  /**
   * Backup file (create .backup copy)
   */
  async backupFile(filePath: string): Promise<string> {
    const backupPath = `${filePath}.backup`;
    await this.copyFile(filePath, backupPath);
    return backupPath;
  }

  /**
   * Restore file from backup
   */
  async restoreFromBackup(filePath: string): Promise<void> {
    const backupPath = `${filePath}.backup`;

    if (await this.fileExists(backupPath)) {
      await this.copyFile(backupPath, filePath);
      await this.deleteFile(backupPath);
      console.log(chalk.green(`🔄 Restored: ${filePath} from backup`));
    } else {
      throw new Error(`Backup file not found: ${backupPath}`);
    }
  }
}