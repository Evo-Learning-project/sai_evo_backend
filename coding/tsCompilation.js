const ts = require("typescript");
const tsConfig = require("./tsconfig.json");
const fs = require("fs");
const getRandomIdentifier = require("./utils").getRandomIdentifier;

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
  return __dirname + "/tmp/" + filename;
}

function compile(source, options) {
  const filename = getRandomIdentifier(20);
  const filepath = getAbsoluteTmpFilePath(filename) + ".ts";

  createTsSourceFile(filepath, source);

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
      return `(${line + 1},${character + 1}): ${message}`;
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
  }

  deleteTmpFiles(filename);
  return res;
}

const tsToJs = (source) => compile(source, tsConfig.compilerOptions);

module.exports = {
  tsToJs,
};
