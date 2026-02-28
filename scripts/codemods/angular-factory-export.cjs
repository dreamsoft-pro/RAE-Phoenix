// CommonJS codemod: AngularJS .factory(...) -> exported functions
const fs = require('fs');
const recast = require('recast');
const t = recast.types;
const b = t.builders;
const babelParser = require('@babel/parser');

const argv = process.argv.slice(2);
const fileIdx = argv.indexOf('--file');
if (fileIdx === -1 || !argv[fileIdx + 1]) {
  console.error('[ERROR] Missing --file <path>');
  process.exit(2);
}
const filePath = argv[fileIdx + 1];
const isDry = argv.includes('--dry-run');

const src = fs.readFileSync(filePath, 'utf8');
const ast = recast.parse(src, {
  parser: {
    parse: (code) =>
      babelParser.parse(code, {
        sourceType: 'script',            // AngularJS pliki często nie są modułami
        allowReturnOutsideFunction: true,
        plugins: []                      // (dodaj 'jsx' gdyby było potrzebne)
      }),
  },
});

let factoryFound = false;
let exported = [];

t.visit(ast, {
  visitCallExpression(path) {
    const callee = path.node.callee;
    // Szukamy: angular.module(...).factory(...)
    const isFactory =
      callee &&
      callee.type === 'MemberExpression' &&
      callee.property &&
      callee.property.name === 'factory' &&
      callee.object &&
      callee.object.type === 'CallExpression' &&
      callee.object.callee &&
      callee.object.callee.type === 'MemberExpression' &&
      callee.object.callee.property &&
      callee.object.callee.property.name === 'module';

    if (!isFactory) return this.traverse(path);

    factoryFound = true;
    const fn = path.node.arguments && path.node.arguments[1];
    if (!fn || fn.type !== 'FunctionExpression') return false; // STOP – nic nie robimy

    const body = Array.isArray(fn.body && fn.body.body) ? fn.body.body : [];

    // 1) Zbierz deklaracje zmiennych z ciała fabryki (hoist)
    const varDecls = body.filter(n => n.type === 'VariableDeclaration');

    // 2) Znajdź return { ... } i zbierz funkcje do eksportu
    const ret = body.find(n => n.type === 'ReturnStatement' && n.argument && n.argument.type === 'ObjectExpression');
    const props = ret ? (ret.argument.properties || []) : [];

    // Mapuj lokalne FunctionDeclaration wg nazwy
    const localFns = new Map();
    body.forEach(n => {
      if (n.type === 'FunctionDeclaration' && n.id && n.id.name) {
        localFns.set(n.id.name, n);
      }
    });

    const exportNodes = [];
    // Najpierw przenieś deklaracje zmiennych (bez export)
    varDecls.forEach(v => exportNodes.push(v));

    // Następnie eksportuj funkcje
    props.forEach(p => {
      if (!p || !p.key || !p.key.name) return;
      const name = p.key.name;
      let fnDecl = null;

      if (p.value && p.value.type === 'Identifier' && localFns.has(name)) {
        // Przypadek: { f1: f1 } – istnieje FunctionDeclaration f1
        fnDecl = localFns.get(name);
      } else if (p.value && p.value.type === 'FunctionExpression') {
        // Przypadek inline: { f2: function(...) {...} }
        fnDecl = b.functionDeclaration(
          b.identifier(name),
          p.value.params || [],
          p.value.body || b.blockStatement([]),
          p.value.generator === true,
          p.value.async === true
        );
      }

      if (fnDecl) {
        exportNodes.push(b.exportNamedDeclaration(fnDecl, []));
        exported.push(name);
      }
    });

    // Zamień całą instrukcję fabryki na zestaw node’ów (zmienne + eksporty)
    const stmtPath = path.parent; // ExpressionStatement
    stmtPath.replace(...exportNodes);

    return false; // NIE wchodź głębiej – zapobiega rekursji
  },
});

// Raport + wynik
console.log(`[DETECTION] factoryFound=${factoryFound} exported=[${exported.join(', ')}]`);
const out = recast.print(ast, { quote: 'single', tabWidth: 2 }).code;

if (isDry) {
  console.log('\n--- MODIFIED (dry-run) ---\n');
  console.log(out);
} else {
  fs.writeFileSync(filePath, out, 'utf8');
  console.log(`[WRITE] ${filePath} updated`);
}
