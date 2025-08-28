#!/usr/bin/env node
// Minimalny, stabilny indexer dla AngularJS (JS + HTML) -> JSONL chunków
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { glob } from "glob";
import { v4 as uuidv4 } from "uuid";
import * as babelParser from "@babel/parser";
import traverse from "@babel/traverse";

const args = process.argv.slice(2);
const rootArgIdx = args.indexOf("--root");
const outArgIdx  = args.indexOf("--out");
if (rootArgIdx === -1 || outArgIdx === -1) {
  console.error("Użycie: node js_html_indexer.mjs --root /ścieżka/do/frontend --out ./data/chunks.jsonl");
  process.exit(1);
}
const ROOT = path.resolve(args[rootArgIdx+1]);
const OUT  = path.resolve(args[outArgIdx+1]);

// Heurystyki komponentów AngularJS
const ANG_METHODS = new Set(["controller","service","factory","directive","filter","config","run"]);

// Pomocnicze: bezpieczne parsowanie JS
function parseJS(code, file) {
  return babelParser.parse(code, {
    sourceType: "unambiguous",
    allowReturnOutsideFunction: true,
    plugins: [
      "jsx",
      "classProperties",
      "objectRestSpread",
      "optionalChaining",
      "dynamicImport"
    ],
    errorRecovery: true
  });
}

function extractDepsFromArray(node) {
  // Wzorzec: ['dep1','dep2', function(dep1, dep2){...}]
  const arr = node.arguments?.[1];
  if (!arr || arr.type !== "ArrayExpression") return null;
  const elms = arr.elements || [];
  if (elms.length === 0) return null;
  const last = elms[elms.length-1];
  if (last.type !== "FunctionExpression" && last.type !== "ArrowFunctionExpression") return null;
  const deps = [];
  for (let i=0; i<elms.length-1; i++) {
    const e = elms[i];
    if (e.type === "StringLiteral") deps.push(e.value);
  }
  return deps;
}

function extractDepsFromFn(node) {
  // Wzorzec: .controller('Name', function($scope, AuthService){})
  const fn = node.arguments?.[1];
  if (fn && (fn.type === "FunctionExpression" || fn.type === "ArrowFunctionExpression")) {
    return (fn.params || []).map(p => p.name).filter(Boolean);
  }
  return null;
}

function findTemplateUrlInDirective(node, code) {
  // Szuka `return { ..., templateUrl: '...' }` w ciele funkcji fabrycznej dyrektywy
  const fn = node.arguments?.[1];
  const body = (fn && (fn.type === "FunctionExpression" || fn.type === "ArrowFunctionExpression")) ? fn.body : null;
  if (!body || body.type !== "BlockStatement") return null;
  for (const st of body.body) {
    if (st.type === "ReturnStatement" && st.argument && st.argument.type === "ObjectExpression") {
      for (const prop of st.argument.properties || []) {
        const key = prop.key?.name || prop.key?.value;
        if (key === "templateUrl") {
          const val = prop.value;
          if (val.type === "StringLiteral") return val.value;
        }
      }
    }
  }
  return null;
}

// Przebieg: JS pliki
async function indexJS(files, out) {
  for (const f of files) {
    const rel = path.relative(ROOT, f);
    const code = fs.readFileSync(f, "utf8");
    let ast;
    try { ast = parseJS(code, f); }
    catch(e) { console.warn("[PARSER] Błąd w", rel, e.message); continue; }

    traverse.default(ast, {
      CallExpression(pathNode) {
        const { node } = pathNode;
        // Oczekujemy np. angular.module(...).controller(...)
        if (node.callee && node.callee.type === "MemberExpression") {
          const prop = node.callee.property;
          const obj  = node.callee.object;
          const methodName = prop?.name;
          if (!ANG_METHODS.has(methodName)) return;

          // Nazwa chunka (np. nazwa kontrolera / serwisu / dyrektywy)
          let chunkName = null;
          const firstArg = node.arguments?.[0];
          if (firstArg && firstArg.type === "StringLiteral") chunkName = firstArg.value;

          // Zależności DI
          let deps = extractDepsFromArray(node) || extractDepsFromFn(node) || [];

          // templateUrl dla dyrektyw
          let templateUrl = null;
          if (methodName === "directive") {
            templateUrl = findTemplateUrlInDirective(node, code);
          }

          // Wytnij fragment kodu (node.loc wymaga sourceLocations)
          const { start, end } = node;
          const snippet = code.slice(start, end);

          const chunk = {
            chunk_id: uuidv4(),
            file_path: rel,
            ast_node_type: "CallExpression",
            chunk_name: chunkName || methodName,
            code_snippet: snippet,
            start_line: node.loc?.start?.line || null,
            end_line: node.loc?.end?.line || null,
            dependencies_di: deps,
            template_url: templateUrl,
            tags: []
          };
          fs.appendFileSync(out, JSON.stringify(chunk) + "\n");
        }
      }
    });
  }
}

// Przebieg: HTML (lekka heurystyka — linie z ng-* i {{ }})
async function indexHTML(files, out) {
  const NG_ATTR = /(data-)?ng-([a-zA-Z0-9-]+)/g;
  const NG_BIND = /\{\{[^}]+\}\}/g;

  for (const f of files) {
    const rel = path.relative(ROOT, f);
    const content = fs.readFileSync(f, "utf8");
    const lines = content.split(/\r?\n/);
    lines.forEach((line, i) => {
      if (NG_ATTR.test(line) || NG_BIND.test(line)) {
        const snippet = line.trim().slice(0, 2000);
        const m = line.match(NG_ATTR);
        const attrs = m ? Array.from(new Set(m.map(x => x.replace(/^data-/, "")))) : [];
        const chunk = {
          chunk_id: uuidv4(),
          file_path: rel,
          ast_node_type: "NgTemplate",
          chunk_name: attrs?.[0] || "ng-binding",
          code_snippet: snippet,
          start_line: i+1,
          end_line: i+1,
          dependencies_di: [],
          template_url: null,
          tags: []
        };
        fs.appendFileSync(out, JSON.stringify(chunk) + "\n");
      }
    });
  }
}

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, ""); // reset

  const jsFiles = await glob("**/*.js", { cwd: ROOT, absolute: true, nodir: true });
  const htmlFiles = await glob("**/*.html", { cwd: ROOT, absolute: true, nodir: true });

  console.log(`[Feniks] JS: ${jsFiles.length} plików, HTML: ${htmlFiles.length} plików`);
  await indexJS(jsFiles, OUT);
  await indexHTML(htmlFiles, OUT);
  console.log(`[Feniks] Zapisano: ${OUT}`);
})();
