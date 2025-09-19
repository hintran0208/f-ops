import { execSync } from 'child_process';
import fs from 'fs-extra';
import path from 'path';

export interface GitInfo {
  isGitRepo: boolean;
  remoteUrl?: string;
  currentBranch?: string;
  repoName?: string;
  hasUncommittedChanges?: boolean;
}

export class GitUtils {
  /**
   * Get comprehensive git information for the current directory
   */
  static getGitInfo(cwd: string = process.cwd()): GitInfo {
    try {
      // Check if .git directory exists
      const gitDir = path.join(cwd, '.git');
      if (!fs.existsSync(gitDir)) {
        return { isGitRepo: false };
      }

      // Get remote URL
      let remoteUrl: string | undefined;
      try {
        remoteUrl = execSync('git config --get remote.origin.url', {
          cwd,
          encoding: 'utf8'
        }).trim();

        // Normalize the URL format
        remoteUrl = this.normalizeGitUrl(remoteUrl);
      } catch (e) {
        // No remote origin configured
      }

      // Get current branch
      let currentBranch: string | undefined;
      try {
        currentBranch = execSync('git rev-parse --abbrev-ref HEAD', {
          cwd,
          encoding: 'utf8'
        }).trim();
      } catch (e) {
        // Unable to get branch
      }

      // Check for uncommitted changes
      let hasUncommittedChanges = false;
      try {
        const status = execSync('git status --porcelain', {
          cwd,
          encoding: 'utf8'
        }).trim();
        hasUncommittedChanges = status.length > 0;
      } catch (e) {
        // Unable to check status
      }

      // Extract repo name from URL or directory
      let repoName: string | undefined;
      if (remoteUrl) {
        repoName = this.extractRepoName(remoteUrl);
      } else {
        repoName = path.basename(cwd);
      }

      return {
        isGitRepo: true,
        remoteUrl,
        currentBranch,
        repoName,
        hasUncommittedChanges
      };

    } catch (error) {
      return { isGitRepo: false };
    }
  }

  /**
   * Normalize git URL to HTTPS format
   */
  private static normalizeGitUrl(url: string): string {
    // Convert SSH to HTTPS format
    if (url.startsWith('git@')) {
      // git@github.com:user/repo.git -> https://github.com/user/repo
      url = url.replace(/^git@([^:]+):/, 'https://$1/');
    }

    // Remove .git suffix
    if (url.endsWith('.git')) {
      url = url.slice(0, -4);
    }

    return url;
  }

  /**
   * Extract repository name from URL
   */
  private static extractRepoName(url: string): string {
    // Extract last two path segments (user/repo)
    const match = url.match(/\/([^\/]+\/[^\/]+)(?:\.git)?$/);
    if (match) {
      return match[1];
    }

    // Fallback: just the last segment
    const segments = url.split('/');
    return segments[segments.length - 1];
  }

  /**
   * Check if current directory has a .gitignore file
   */
  static hasGitignore(cwd: string = process.cwd()): boolean {
    return fs.existsSync(path.join(cwd, '.gitignore'));
  }

  /**
   * Get git repository root directory
   */
  static getRepoRoot(cwd: string = process.cwd()): string | null {
    try {
      const root = execSync('git rev-parse --show-toplevel', {
        cwd,
        encoding: 'utf8'
      }).trim();
      return root;
    } catch (e) {
      return null;
    }
  }

  /**
   * Check if the repository is clean (no uncommitted changes)
   */
  static isRepoClean(cwd: string = process.cwd()): boolean {
    try {
      const status = execSync('git status --porcelain', {
        cwd,
        encoding: 'utf8'
      }).trim();
      return status.length === 0;
    } catch (e) {
      return false;
    }
  }

  /**
   * Get list of modified files
   */
  static getModifiedFiles(cwd: string = process.cwd()): string[] {
    try {
      const status = execSync('git status --porcelain', {
        cwd,
        encoding: 'utf8'
      }).trim();

      if (!status) return [];

      return status
        .split('\n')
        .map(line => line.substring(3)) // Remove status prefix (e.g., " M ", "??")
        .filter(file => file.length > 0);
    } catch (e) {
      return [];
    }
  }

  /**
   * Generate a meaningful repository identifier for API calls
   */
  static getRepoIdentifier(cwd: string = process.cwd()): string {
    const gitInfo = this.getGitInfo(cwd);

    if (gitInfo.remoteUrl) {
      return gitInfo.remoteUrl;
    }

    // For local repositories without remote, create a special local URL format
    // that includes the actual path for the backend to analyze
    const repoName = gitInfo.repoName || path.basename(cwd);
    return `local:${cwd}`;
  }

  /**
   * Get repository info for API calls including both identifier and local path
   */
  static getRepositoryInfo(cwd: string = process.cwd()): { repoUrl: string; localPath?: string } {
    const gitInfo = this.getGitInfo(cwd);

    if (gitInfo.remoteUrl) {
      // Remote repository
      return { repoUrl: gitInfo.remoteUrl };
    }

    // Local repository - provide both identifier and actual path
    const repoName = gitInfo.repoName || path.basename(cwd);
    return {
      repoUrl: `https://github.com/local/${repoName}`,
      localPath: cwd
    };
  }
}