const ts = require("typescript");
const tsConfig = require("./tsconfig.json");
const fs = require("fs");
const getRandomIdentifier = require("./utils").getRandomIdentifier;

const ENV_DECLARATION_SEPARATOR = "/*" + getRandomIdentifier(20) + "*/";

function createTsSourceFile(filename, source) {
  fs.writeFileSync(filename, source);
  return filename;
}

function deleteTmpFiles(filename) {
  try {
    fs.unlinkSync(getAbsoluteTmpFilePath(filename) + ".ts");
    fs.unlinkSync(getAbsoluteTmpFilePath(filename) + ".js");
  } catch {}
}

function getAbsoluteTmpFilePath(filename) {
  return getTmpFileDir() + filename;
}

function getTmpFileDir() {
  return __dirname + "/tmp/";
}

function addEnvironmentDeclarations(source, environment) {
  if (!environment || environment.length === 0) {
    return source;
  }

  const envDeclarations = environment
    .map((d) => `const ${d}: any = {};`)
    .join("");

  return envDeclarations + "\n" + ENV_DECLARATION_SEPARATOR + "\n" + source;
}

function compile(source, options, environment) {
  const filename = getRandomIdentifier(20);
  const filepath = getAbsoluteTmpFilePath(filename) + ".ts";

  if (!fs.existsSync(getTmpFileDir())) {
    fs.mkdirSync(getTmpFileDir(), 0744, { recursive: true });
  }

  // add dummy declarations for the identifiers in `environment` to prevent compilation errors
  const sourceWithEnvironmentDeclarations = addEnvironmentDeclarations(
    source,
    environment
  );

  createTsSourceFile(filepath, sourceWithEnvironmentDeclarations);

  const defaultCompilerHost = ts.createCompilerHost({});
  const program = ts.createProgram([filepath], options, defaultCompilerHost);
  const emitResult = program.emit();

  const allDiagnostics = ts
    .getPreEmitDiagnostics(program)
    .concat(emitResult.diagnostics);

  const processedDiagnostics = allDiagnostics.map((diagnostic) => {
    if (diagnostic.file) {
      let { line, character } = ts.getLineAndCharacterOfPosition(
        diagnostic.file,
        diagnostic.start
      );
      let message = ts.flattenDiagnosticMessageText(
        diagnostic.messageText,
        "\n"
      );
      return `(on line ${line + 1}, at position ${character + 1}): ${message}`;
    } else {
      return ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n");
    }
  });

  const res = {
    compilationErrors: processedDiagnostics,
  };

  if (processedDiagnostics.length === 0) {
    res.compiledCode = String(
      fs.readFileSync(getAbsoluteTmpFilePath(filename) + ".js")
    );
    if (environment && environment.length > 0) {
      // strip first line containing dummy declarations from the environment
      const declarationLine = res.compiledCode.split(
        ENV_DECLARATION_SEPARATOR
      )[0];
      res.compiledCode = res.compiledCode.substring(
        declarationLine.length + ENV_DECLARATION_SEPARATOR.length
      );
    }
  }

  deleteTmpFiles(filename);
  return res;
}

const tsToJs = (source, environment) =>
  compile(source, tsConfig.compilerOptions, environment);

module.exports = {
  tsToJs,
};
