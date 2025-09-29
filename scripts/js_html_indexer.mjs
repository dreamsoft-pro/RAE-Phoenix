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

          // --- Nowe funkcjonalności ---

          // 1. Wyszukiwanie endpointów API w ciele funkcji
          const apiEndpoints = [];
          const functionBody = pathNode.get("arguments.1.body");
          if (functionBody) {
            functionBody.traverse({
              CallExpression(innerPath) {
                const callee = innerPath.get("callee");
                if (callee.isMemberExpression() && callee.get("object").isIdentifier({ name: "$http" })) {
                  const firstArg = innerPath.get("arguments.0");
                  if (firstArg && firstArg.isStringLiteral()) {
                    apiEndpoints.push(firstArg.node.value);
                  }
                }
              }
            });
          }

          // 2. Generowanie sugestii migracyjnych
          let migrationSuggestion = {};
          switch (methodName) {
            case "service":
            case "factory":
              migrationSuggestion = { target: "Custom Hook (e.g., useSWR)", notes: "Replace $http with fetch/axios and wrap logic in a reusable data-fetching hook." };
              break;
            case "controller":
              migrationSuggestion = { target: "Functional React Component", notes: "State logic should be managed by hooks like useState, useReducer, or a state management library." };
              break;
            case "directive":
              migrationSuggestion = { target: "React Component", notes: "Can be a functional component. DOM manipulations should be replaced with declarative JSX and state." };
              break;
            case "filter":
              migrationSuggestion = { target: "Utility Function", notes: "Can be a simple exported JavaScript function that takes a value and returns a transformed value." };
              break;
          }

          // Wytnij fragment kodu i komentarze (sprawdzając też węzeł nadrzędny)
          const { start, end } = node;
          const snippet = code.slice(start, end);
          const parentNode = pathNode.parentPath.node;
          const allComments = (parentNode.leadingComments || []).concat(node.leadingComments || []);
          const comments = allComments.map(c => ` * ${c.value.trim()}`).join("\n");
          const fullSnippet = (comments ? `/**\n${comments}\n */\n` : "") + snippet;

          const chunk = {
            chunk_id: uuidv4(),
            file_path: rel,
            ast_node_type: "CallExpression",
            chunk_name: chunkName || methodName,
            code_snippet: fullSnippet,
            start_line: node.loc?.start?.line || null,
            end_line: node.loc?.end?.line || null,
            dependencies_di: deps,
            template_url: templateUrl,
            // Nowe pola
            api_endpoints: apiEndpoints,
            migration_suggestion: migrationSuggestion,
            // Stare pola
            tags: [],
            comments: allComments.map(c => c.value.trim()).join("\n"),
          };
          fs.appendFileSync(out, JSON.stringify(chunk) + "\n");
        }
      }
    });
  }
}

// Przebieg: HTML (ulepszona heurystyka semantyczna)
async function indexHTML(files, out) {
  for (const f of files) {
    const rel = path.relative(ROOT, f);
    const content = fs.readFileSync(f, "utf8");

    // Dziel na większe bloki, np. po <form>, <section>, lub div z klasą "container" lub "row"
    const chunks = content.split(/(?=<form|<section|<div\s+(?:class|ng-class)\s*=\s*['"][^'"]*\b(?:container|row|page|modal-body)\b[^'"]*['"])/);

    let currentLine = 1;
    for (const part of chunks) {
      if (!part.trim()) continue;

      const lines = part.split(/\r?\n/);
      const startLine = currentLine;
      const endLine = currentLine + lines.length - 1;

      let chunkName = "html_section";
      const idMatch = part.match(/id="([^"]+)"/);
      if (idMatch) {
        chunkName = idMatch[1];
      } else {
        const classMatch = part.match(/class="([^"]+)"/);
        if (classMatch) chunkName = classMatch[1].split(" ")[0];
      }

      const chunk = {
        chunk_id: uuidv4(),
        file_path: rel,
        ast_node_type: "NgTemplate",
        chunk_name: chunkName,
        code_snippet: part.trim(),
        start_line: startLine,
        end_line: endLine,
        dependencies_di: [],
        template_url: null,
        tags: [],
        comments: ""
      };
      fs.appendFileSync(out, JSON.stringify(chunk) + "\n");

      currentLine = endLine + 1;
    }
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
