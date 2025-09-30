const fs = require('fs');
const { parse, print, visit } = require('recast');
const babelParser = require('@babel/parser');

const argv = process.argv.slice(2);
const filePath = argv[argv.indexOf('--file') + 1];
const dryRun = argv.includes('--dry-run');

if (!filePath) {
  console.error('[ERROR] Nie podano ścieżki do pliku. Użyj --file <path>');
  process.exit(1);
}

const code = fs.readFileSync(filePath, 'utf-8');
const ast = parse(code, {
  parser: {
    parse: (source) => babelParser.parse(source, {
        sourceType: 'module',
    })
  }
});

let factoryFound = false;
let detectedFunctionNames = [];

visit(ast, {
  visitCallExpression(path) {
    const callee = path.node.callee;
    if (
      callee.type === 'MemberExpression' &&
      callee.property.name === 'factory' &&
      callee.object.type === 'CallExpression' &&
      callee.object.callee.type === 'MemberExpression' &&
      callee.object.callee.property.name === 'module'
    ) {
      factoryFound = true;
      const factoryFunc = path.node.arguments[1];

      if (factoryFunc && factoryFunc.type === 'FunctionExpression') {
        visit(factoryFunc, {
          visitReturnStatement(returnPath) {
            if (returnPath.node.argument.type === 'ObjectExpression') {
              detectedFunctionNames = returnPath.node.argument.properties.map(p => p.key.name);
              returnPath.prune();
            }
            this.traverse(returnPath);
          }
        });

        const factoryBody = factoryFunc.body.body;
        path.parentPath.replace(...factoryBody);
      }
      return false;
    }
    this.traverse(path);
  }
});

if (factoryFound) {
    visit(ast, {
        visitFunctionDeclaration(path) {
            if (detectedFunctionNames.includes(path.node.id.name)) {
                path.replace({
                    type: 'ExportNamedDeclaration',
                    declaration: path.node,
                    specifiers: [],
                    source: null
                });
                return false;
        }
    });
}

console.log(`[DETEKCJA] Czy znaleziono fabrykę: ${factoryFound}`);
if(detectedFunctionNames.length > 0) {
    console.log(`[DETEKCJA] Wykryte nazwy funkcji: ${detectedFunctionNames.join(', ')}`);
}

const output = print(ast, { tabWidth: 4, quote: 'single' });

if (dryRun) {
    console.log('\n--- PATCH (DRY-RUN) ---\n');
    console.log(output.code);
} else {
    fs.writeFileSync(filePath, output.code, 'utf-8');
    console.log(`[SUCCESS] Plik ${filePath} został zmodyfikowany.`);
}
