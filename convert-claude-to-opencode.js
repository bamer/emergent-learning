#!/usr/bin/env node

/**
 * convert-opencode-to-opencode.js
 * Converts Claude Code format to OpenCode.ai format
 *
 * Usage: node convert-opencode-to-opencode.js [--watch]
 */

const fs = require('fs');
const path = require('path');

// Configuration - Use absolute paths from the script location
const SCRIPT_DIR = __dirname;
const OUTPUT_DIR = path.join(SCRIPT_DIR, 'converted-opencode');

// OpenCode frontmatter fields (subset of Claude fields)
const OPENCODE_FIELDS = ['name', 'description', 'tools', 'model', 'permissionMode', 'skills', 'hooks'];

console.log('🚀 Claude Code → OpenCode.ai Converter');
console.log(`   Output: ${OUTPUT_DIR}\n`);

/**
 * Parses YAML frontmatter from markdown
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { frontmatter: null, content };
  
  const yaml = match[1];
  const body = match[2];
  
  const frontmatter = {};
  yaml.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > -1) {
      const key = line.slice(0, colonIndex).trim();
      let value = line.slice(colonIndex + 1).trim();
      
      // Parse arrays
      if (value.startsWith('[') && value.endsWith(']')) {
        value = value.slice(1, -1).split(',').map(v => v.trim().replace(/"/g, ''));
      }
      
      frontmatter[key] = value;
    }
  });
  
  return { frontmatter, body };
}

/**
 * Converts path references from ~/.opencode to ~/.opencode in markdown body
 */
function convertPathsInBody(body) {
  return body
    // Convert ~/.opencode/emergent-learning to ~/.opencode/emergent-learning
    .replace(/~\/\.opencode\/emergent-learning/g, '~/.opencode/emergent-learning')
    // Convert /home/user/.opencode/emergent-learning to /home/user/.opencode/emergent-learning
    .replace(/\/\.opencode\/emergent-learning/g, '/.opencode/emergent-learning')
    // Convert opencode CLI references (keep opencode/big-pickle model)
    .replace(/opencode --print --model (nvidia/qwen/qwen3-next-80b-a3b-instruct|opus|sonnet)/g, 'opencode --print --model opencode/big-pickle')
    .replace(/opencode --print --model gpt-4/g, 'opencode --print --model opencode/big-pickle')
    // Update python command references
    .replace(/python .*\/.opencode\/emergent-learning\//g, (match) => {
      return match.replace(/\.opencode/, '.opencode');
    });
}

/**
 * Converts Claude frontmatter to OpenCode format
 */
function convertFrontmatter(opencodeFrontmatter) {
  const opencode = {};
  
  // Map Claude fields to OpenCode fields
  opencode.name = opencodeFrontmatter.name;
  opencode.description = opencodeFrontmatter.description;
  
  // Map tools from Claude to OpenCode permissions
  if (opencodeFrontmatter.tools) {
    const tools = Array.isArray(opencodeFrontmatter.tools) 
      ? opencodeFrontmatter.tools 
      : opencodeFrontmatter.tools.split(',').map(t => t.trim());
    
    // Convert to OpenCode permissions format
    opencode.permissions = {
      read: tools.includes('Read'),
      grep: tools.includes('Grep'),
      glob: tools.includes('Glob'),
      edit: tools.includes('Edit'),
      write: tools.includes('Write'),
      bash: tools.includes('Bash')
    };
  }
  
  // Map model from Claude aliases to OpenCode format
  opencode.model = mapModel(opencodeFrontmatter.model);
  
  // Map permissionMode
  opencode.mode = opencodeFrontmatter.permissionMode === 'plan' ? 'subagent' : 'default';
  
  // Map skills (if present)
  if (opencodeFrontmatter.skills) {
    opencode.skills = Array.isArray(opencodeFrontmatter.skills) 
      ? opencodeFrontmatter.skills 
      : opencodeFrontmatter.skills.split(',').map(s => s.trim());
  }
  
  // Map hooks (if present)
  if (opencodeFrontmatter.hooks) {
    opencode.hooks = Array.isArray(opencodeFrontmatter.hooks) 
      ? opencodeFrontmatter.hooks 
      : opencodeFrontmatter.hooks.split(',').map(h => h.trim());
  }
  
  return opencode;
}

/**
 * Maps Claude model aliases to OpenCode model names
 */
function mapModel(model) {
  const modelMap = {
    'sonnet': 'opencode/big-pickle',
    'opus': 'opencode/big-pickle',
    'nvidia/qwen/qwen3-next-80b-a3b-instruct': 'opencode/big-pickle',
    'gpt-4': 'opencode/big-pickle',
    'gpt-4o': 'opencode/big-pickle',
  };
  return modelMap[model] || 'opencode/big-pickle';
}

/**
 * Generates OpenCode markdown from converted data
 */
function generateOpenCodeMarkdown(opencodeFrontmatter, body) {
  const fm = Object.entries(opencodeFrontmatter)
    .map(([key, value]) => {
      if (key === 'permissions') {
        // Special handling for permissions object
        const perms = Object.entries(value)
          .filter(([_, allowed]) => allowed)
          .map(([perm, _]) => perm)
          .join(', ');
        return `permissions: [${perms}]`;
      }
      if (Array.isArray(value)) {
        return `${key}: [${value.map(v => `"${v}"`).join(', ')}]`;
      }
      return `${key}: "${value}"`;
    })
    .join('\n');
  
  return `---\n${fm}\n---\n\n${body}`;
}

/**
 * Recursively finds all .md files in a directory
 */
function findMarkdownFiles(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findMarkdownFiles(fullPath, files);
    } else if (entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

/**
 * Processes a single agent file
 */
function processAgent(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const { frontmatter, body } = parseFrontmatter(content);
  
  if (!frontmatter) {
    console.log(`⚠️  Skipping ${filePath} (no frontmatter)`);
    return;
  }
  
  const opencodeFrontmatter = convertFrontmatter(frontmatter);
  
  // Convert paths in body content
  const convertedBody = convertPathsInBody(body);
  
  const opencodeMarkdown = generateOpenCodeMarkdown(opencodeFrontmatter, convertedBody);
  
  // Determine output path
  const relativePath = path.relative(process.cwd(), filePath);
  const outputPath = path.join(OUTPUT_DIR, relativePath);
  
  // Ensure output directory exists
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  
  fs.writeFileSync(outputPath, opencodeMarkdown);
  console.log(`✅ Converted: ${relativePath}`);
}

/**
 * Main conversion function
 */
function convert() {
  // Clean output directory
  if (fs.existsSync(OUTPUT_DIR)) fs.rmSync(OUTPUT_DIR, { recursive: true });
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  
  console.log('📦 Converting Claude agents to OpenCode format...\n');
  
  // Process all .md files in current directory and subdirectories
  const agentFiles = findMarkdownFiles(process.cwd());
  const opencodeFiles = agentFiles.filter(file => {
    const content = fs.readFileSync(file, 'utf8');
    const { frontmatter } = parseFrontmatter(content);
    return frontmatter && frontmatter.name && frontmatter.description;
  });
  
  if (opencodeFiles.length === 0) {
    console.log('No Claude agent files found. Looking for .md files with frontmatter...');
    return;
  }
  
  opencodeFiles.forEach(processAgent);
  
  console.log('\n✨ Conversion complete!');
  console.log(`   Output: ${OUTPUT_DIR}`);
  console.log('   Files converted to OpenCode.ai format with proper permissions and model mapping.');
}

// Run conversion
convert();