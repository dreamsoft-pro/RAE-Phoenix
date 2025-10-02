// scripts/js_html_indexer.mjs
// ESM Node 18+
// Usage: node scripts/js_html_indexer.mjs --root <frontend-root> --out <out-jsonl>
import fs from 'fs';
import fsp from 'fs/promises';
import path from 'path';
import fg from 'fast-glob';
import * as babelParser from '@babel/parser';
import traverse from '@babel/traverse';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { root: null, out: null };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--root') out.root = args[++i];
    else if (args[i] === '--out') out.out = args[++i];
  }
  if (!out.root) throw new Error('Missing --root');
  if (!out.out) throw new Error('Missing --out');
  return out;
}

function readFileSafe(p) {
  try { return fs.readFileSync(p, 'utf8'); }
  catch { return null; }
}

function toUnix(p) { return p.split(path.sep).join('/'); }

function decisionCount(node) {
  // Simple cyclomatic complexity approximation
  let count = 1;
  if (!node) return count;
  traverse.default(node, {
    enter(path) {
      switch (path.node.type) {
        case 'IfStatement':
        case 'ForStatement':
        case 'ForInStatement':
        case 'ForOfStatement':
        case 'WhileStatement':
        case 'DoWhileStatement':
        case 'CatchClause':
        case 'ConditionalExpression':
          count++; break;
        case 'LogicalExpression':
          if (path.node.operator === '||' || path.node.operator === '&&') count++;
          break;
        case 'SwitchCase':
          if (path.node.test) count++;
          break;
      }
    }
  });
  return count;
}

function businessTagsFromName(name, file) {
  const s = (name || '' + ' ' + (file || '')).toLowerCase();
  const tags = new Set();
  const addIf = (re, t) => { if (re.test(s)) tags.add(t); };
  addIf(/\bauth|login|logout|token|session\b/, 'authentication');
  addIf(/\bpay|payment|checkout|transaction|billing\b/, 'payment');
  addIf(/\bprice|pric(ing)|discount|promo|vat|tax\b/, 'pricing');
  addIf(/\bcart|basket\b/, 'cart');
  addIf(/\border|shipment|delivery\b/, 'order');
  addIf(/\binventory|stock|warehouse\b/, 'inventory');
  addIf(/\buser|account|profile\b/, 'user');
  addIf(/\breport|analytics|metric|kpi\b/, 'analytics');
  return Array.from(tags);
}

function getObjectKeys(node) {
  if (!node || node.type !== 'ObjectExpression') return [];
  return node.properties.map(p => {
    if (p.type === 'SpreadElement') return null; // Ignore spread elements for now
    const key = p.key;
    if (key) {
      if (key.type === 'Identifier') return key.name;
      if (key.type === 'StringLiteral') return key.value;
    }
    return null;
  }).filter(Boolean);
}

function evaluateUrlNode(node) {
    if (!node) return '';
    switch (node.type) {
        case 'StringLiteral':
            return node.value;
        case 'Identifier':
            return `\${{node.name}}`;
        case 'MemberExpression':
            const obj = node.object.name || '...';
            const prop = node.property.name || '...';
            return `\${{obj}.${prop}}`;
        case 'BinaryExpression':
            if (node.operator === '+') {
                return evaluateUrlNode(node.left) + evaluateUrlNode(node.right);
            }
            break;
        case 'TemplateLiteral':
            return node.quasis.map(q => q.value.cooked).join('\${...}');
        case 'CallExpression':
            if (node.callee.type === 'MemberExpression' && node.callee.property.name === 'join') {
                if (node.callee.object.type === 'ArrayExpression') {
                    return node.callee.object.elements.map(evaluateUrlNode).join(node.arguments[0].value);
                }
            }
            return '{...}';
    }
    return '{...}';
}


function apiEndpointsFromCall(calleeName, args) {
  const endpoints = [];
  if (!args || args.length === 0) return [];

  let url, method, dataKeys = [], paramKeys = [];

  // Case 1: $http.get(url, config), $http.post(url, data, config)
  const match = calleeName.match(/\$http\.(get|delete|head|jsonp|post|put|patch)/);
  if (match) {
    method = match[1].toUpperCase();
    const urlArg = args[0];
    url = evaluateUrlNode(urlArg);
    console.log('apiEndpointsFromCall: url=', url, 'method=', method);

    const isPostLike = ['POST', 'PUT', 'PATCH'].includes(method);
    const dataArg = isPostLike ? args[1] : null;
    const configArg = isPostLike ? args[2] : args[1];

    if (dataArg && dataArg.type === 'ObjectExpression') {
      dataKeys = getObjectKeys(dataArg);
    }

    if (configArg && configArg.type === 'ObjectExpression') {
      const paramsProp = configArg.properties.find(p => p.key && (p.key.name === 'params' || p.key.value === 'params'));
      if (paramsProp && paramsProp.value.type === 'ObjectExpression') {
        paramKeys = getObjectKeys(paramsProp.value);
      }
    }

  } else if (calleeName === '$http') {
    // Case 2: $http({ method, url, ... })
    const config = args[0];
    if (config && config.type === 'ObjectExpression') {
      for (const prop of config.properties) {
        if (prop.type === 'SpreadElement') continue;
        const key = prop.key?.name || prop.key?.value;
        if (key === 'method' && prop.value.type === 'StringLiteral') {
          method = prop.value.value.toUpperCase();
        }
        if (key === 'url') {
          url = evaluateUrlNode(prop.value);
        }
        if (key === 'data' && prop.value.type === 'ObjectExpression') {
          dataKeys = getObjectKeys(prop.value);
        }
        if (key === 'params') {
            if (prop.value.type === 'ObjectExpression') {
                paramKeys = getObjectKeys(prop.value);
            } else if (prop.value.type === 'Identifier') {
                // Cannot resolve variable, but we know params exist
                paramKeys = ['...'];
            }
        }
      }
      console.log('apiEndpointsFromCall: url=', url, 'method=', method);
    }
  }

  if (url && method && (url.includes('/api/') || url.startsWith('http') || url.startsWith('${'))) {
    endpoints.push({ url, method, dataKeys, paramKeys });
  }
  return endpoints;
}

function calleeNameFromNode(node) {
  if (!node) return null;
  if (node.type === 'Identifier') return node.name;
  if (node.type === 'MemberExpression') {
    const obj = calleeNameFromNode(node.object);
    const prop = node.property && (node.property.name || (node.property.value ?? ''));
    if (obj && prop) return `${obj}.${prop}`;
  }
  if (node.type === 'OptionalMemberExpression') {
    const obj = calleeNameFromNode(node.object);
    const prop = node.property && (node.property.name || (node.property.value ?? ''));
    if (obj && prop) return `${obj}.${prop}`;
  }
  return null;
}

function parseHTML(filePath, code) {
  const file = toUnix(filePath);
  const id = `${file}:1-${code.split('\n').length}:html:whole-file`;
  const record = {
    id,
    filePath: file,
    module: null,
    name: path.basename(file),
    kind: 'template',
    language: 'html',
    nodeType: 'File',
    dependencies: [],
    antiPatterns: [],
    text: code,
    start: 1,
    end: code.split('\n').length,
    route: null,
    symbol: path.basename(file),
    metadata: {
      calls_functions: [],
      api_endpoints: [],
      ui_routes: [],
      cyclomatic_complexity: 1,
      eventfulness: {
          watchers: 0,
          emits: 0,
          broadcasts: 0
      },
      summary_en: null,
      business_tags: []
    }
  };
  return [record];
}

function parseJS(filePath, code, modulesCtx) {
  const ast = babelParser.parse(code, {
    sourceType: 'module',
    plugins: ['jsx', 'classProperties', 'objectRestSpread', 'optionalChaining']
  });
  const chunks = [];
  const routes = [];

  function pushChunk({id, kind, name, module, start, end, text, deps, language}) {
    const file = toUnix(filePath);
    const calls = new Set();
    const api = new Set();
    let complexity = 1;
    let watchers = 0, emits = 0, broadcasts = 0;

    traverse.default(ast, {
      enter(p) {
        // Restrict to function range if provided
        if (start != null && end != null) {
          const n = p.node;
          if (!n.loc) return;
          const s = n.loc.start.line, e = n.loc.end.line;
          if (e < start || s > end) p.skip();
        }
        if (p.isCallExpression()) {
          const c = p.node.callee;
          const name = calleeNameFromNode(c);
          if (name) {
            if (name.endsWith('$watch')) watchers++;
            if (name.endsWith('$emit')) emits++;
            if (name.endsWith('$broadcast')) broadcasts++;
            calls.add(name);
          }
          // API endpoints
          if (name && (/^\$?http$/.test(name) || /^\$?http\./.test(name))) {
            apiEndpointsFromCall(name, p.node.arguments).forEach(a => api.add(JSON.stringify(a)));
          }
        }
      }
    });

    // Rough complexity on sliced AST region
    if (start != null && end != null) {
      complexity = decisionCount(ast);
    } else {
      complexity = decisionCount(ast);
    }

    const business_tags = businessTagsFromName(name, file);
    const record = {
      id,
      filePath: file,
      module,
      name,
      kind,
      language,
      nodeType: 'Function',
      dependencies: deps.map(d => ({ type: 'di', value: d })) || [],
      antiPatterns: [],
      text,
      start: start ?? 1,
      end: end ?? (code.split('\n').length),
      route: null,
      symbol: name,
      metadata: {
        calls_functions: Array.from(calls),
        api_endpoints: Array.from(api).map(a => JSON.parse(a)),
        ui_routes: [],
        cyclomatic_complexity: complexity,
        eventfulness: {
            watchers,
            emits,
            broadcasts
        },
        summary_en: null,
        business_tags
      }
    };
    chunks.push(record);
  }

  function angularDIParams(fnNode) {
    if (!fnNode) return [];
    if (fnNode.type === 'FunctionExpression' || fnNode.type === 'ArrowFunctionExpression') {
      return (fnNode.params || []).map(p => p.name).filter(Boolean);
    }
    return [];
  }

  traverse.default(ast, {
    CallExpression(p) {
      const callee = p.node.callee;
      if (callee.type === 'MemberExpression') {
        const prop = callee.property?.name || callee.property?.value;
        if (!prop) return;
        if (prop === 'module' && callee.object?.name === 'angular') {
          const modArg = p.node.arguments?.[0];
          if (modArg?.type === 'StringLiteral') {
            modulesCtx.currentModule = modArg.value;
          }
        }
        const propName = String(prop);
        const isNgDef = ['controller','service','factory','directive','filter','component','config'].includes(propName);
        if (isNgDef) {
          const args = p.node.arguments || [];
          const nameArg = args[0];
          const defArg = args.slice(-1)[0];
          const name = nameArg && nameArg.type === 'StringLiteral' ? nameArg.value : null;
          const moduleName = modulesCtx.currentModule || null;
          let fnNode = defArg;
          let deps = [];
          if (defArg && defArg.type === 'ArrayExpression') {
            const elems = defArg.elements || [];
            const last = elems[elems.length - 1];
            fnNode = last;
            deps = elems.slice(0, -1).map(e => e.value).filter(Boolean);
          } else {
            deps = angularDIParams(defArg);
          }
          const { start, end } = fnNode?.loc || p.node.loc || {start:{line:1}, end:{line: code.split('\n').length}};
          const lines = code.split('\n').slice(start.line - 1, end.line).join('\n');
          const id = `${toUnix(filePath)}:${start.line}-${end.line}:${propName}:${name ?? 'anonymous'}`;
          const kindMap = {controller:'component', component:'component', service:'service', factory:'service', directive:'directive', filter:'filter', config:'route'};
          pushChunk({id, kind: kindMap[propName] || 'util', name: name ?? 'anonymous', module: moduleName, start: start.line, end: end.line, text: lines, deps, language: 'javascript'});
        }
      }
    }
  });

  traverse.default(ast, {
    CallExpression(p) {
      const callee = p.node.callee;
      if (callee.type === 'MemberExpression') {
        const objName = callee.object?.name || callee.object?.property?.name;
        const propName = callee.property?.name;
        if (objName === '$stateProvider' && propName === 'state') {
          const [stateName, cfg] = p.node.arguments || [];
          let url = null, controller = null, templateUrl = null;
          if (cfg && cfg.type === 'ObjectExpression') {
            for (const prop of cfg.properties || []) {
              const key = prop.key?.name || prop.key?.value;
              if (key === 'url' && prop.value.type === 'StringLiteral') url = prop.value.value;
              if (key === 'controller' && prop.value.type === 'StringLiteral') controller = prop.value.value;
              if (key === 'templateUrl' && prop.value.type === 'StringLiteral') templateUrl = prop.value.value;
            }
          }
          const sName = stateName && stateName.type === 'StringLiteral' ? stateName.value : null;
          routes.push({ type: 'ui-router', state: sName, url, controller, templateUrl });
        }
        if (objName === '$routeProvider' && propName === 'when') {
          const [urlArg, cfg] = p.node.arguments || [];
          let url = null, controller = null, templateUrl = null;
          if (urlArg?.type === 'StringLiteral') url = urlArg.value;
          if (cfg && cfg.type === 'ObjectExpression') {
            for (const prop of cfg.properties || []) {
              const key = prop.key?.name || prop.key?.value;
              if (key === 'controller' && prop.value.type === 'StringLiteral') controller = prop.value.value;
              if (key === 'templateUrl' && prop.value.type === 'StringLiteral') templateUrl = prop.value.value;
            }
          }
          routes.push({ type: 'ng-route', state: null, url, controller, templateUrl });
        }
      }
    }
  });

  if (routes.length && chunks.length) {
    const byCtrl = new Map();
    for (const r of routes) {
      if (r.controller) {
        const arr = byCtrl.get(r.controller) || [];
        arr.push(r.url);
        byCtrl.set(r.controller, arr);
      }
    }
    for (const ch of chunks) {
      const urls = byCtrl.get(ch.name) || [];
      if (urls.length) {
        ch.metadata.ui_routes = Array.from(new Set([...(ch.metadata.ui_routes || []), ...urls]));
      }
    }
    for (const r of routes) {
      const id = `${toUnix(filePath)}:route:${r.url || r.state}`;
      const text = `// route: ${r.type} ${r.state ?? ''} ${r.url ?? ''} controller=${r.controller ?? ''}`;
      chunks.push({
        id,
        filePath: toUnix(filePath),
        module: null,
        name: r.controller || r.state || (r.url ?? 'route'),
        kind: 'route',
        language: 'javascript',
        nodeType: 'Object',
        dependencies: [],
        antiPatterns: [],
        text,
        start: 1, end: 1,
        route: r.url || r.state,
        symbol: r.controller || r.state,
        metadata: {
          calls_functions: [],
          api_endpoints: [],
          ui_routes: r.url ? [r.url] : [],
          cyclomatic_complexity: 1,
          summary_en: null,
          business_tags: businessTagsFromName(r.controller || r.state, filePath)
        }
      });
    }
  }

  return chunks;
}

async function main() {
  const args = parseArgs();
  const root = path.resolve(args.root);
  const outPath = path.resolve(args.out);
  await fsp.mkdir(path.dirname(outPath), { recursive: true });

  const patterns = [
    toUnix(path.join(root, '**/*.js')),
    toUnix(path.join(root, '**/*.html')),
  ];
  const entries = await fg(patterns, { dot: false, onlyFiles: true });
  let total = 0;
  const out = fs.createWriteStream(outPath, { flags: 'w', encoding: 'utf8' });

  for (const file of entries) {
    const code = readFileSafe(file);
    if (!code) continue;
    const modulesCtx = { currentModule: null };
    try {
      let recs = [];
      if (file.endsWith('.js')) {
        recs = parseJS(file, code, modulesCtx);
      } else if (file.endsWith('.html')) {
        recs = parseHTML(file, code);
      }

      for (const r of recs) {
        out.write(JSON.stringify(r) + '\n');
        total++;
      }
    } catch (e) {
      out.write(JSON.stringify({ error: String(e), filePath: toUnix(file) }) + '\n');
    }
  }
  out.end();
  console.log(`[OK] Indexed ${entries.length} files → ${total} records at ${outPath}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(e => { console.error(e); process.exit(1); });
}