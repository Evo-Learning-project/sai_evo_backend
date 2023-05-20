// The VM2 module allows execution of arbitrary code safely using
// a sandboxed, secure virtual machine
const { NodeVM } = require("vm2");
const compileTsToJs = require("./tsCompilation").tsToJs;
const utils = require("./utils");

const SANDBOX_TIMEOUT = utils.SANDBOX_TIMEOUT;

const userCode = process.argv[2];
const compileFromTs = JSON.parse(process.argv[3] ?? "false");
const streamOutput = JSON.parse(process.argv[4] ?? "false");

// to take track of elapsed time
const beginEndTime = [];
function reportTime() {
  beginEndTime.push(Date.now());
}
function getElapsedTime() {
  return beginEndTime[1] - beginEndTime[0];
}
const REPORT_TIME_IDENTIFIER = utils.getRandomIdentifier(32);

// instantiation of the vm that'll run the user-submitted program
const safeVm = new NodeVM({
  console: "redirect", // redirect console to capture output
  timeout: SANDBOX_TIMEOUT, // set timeout to prevent endless loops from running forever
  sandbox: {
    [REPORT_TIME_IDENTIFIER]: reportTime,
  },
  wrapper: "none",
});

// capture program output
const programOutput = {
  log: [],
  error: [],
  warn: [],
  dir: [],
  info: [],
  debug: [],
  trace: [],
};

// record program output
function onOutput(type, ...data) {
  // TODO extra info such as line number, timestamp, etc.
  programOutput[type].push({ data });
  if (streamOutput) {
    console.log(JSON.stringify({ type, data: JSON.stringify(data) }));
  }
}

// add listeners to capture program output
["log", "error", "warn", "dir", "info", "debug", "trace"].forEach((type) => {
  safeVm.on(`console.${type}`, (...data) => onOutput(type, ...data));
});

const RET_IDENTIFIER = utils.getRandomIdentifier(32);
let machineProgram = `${REPORT_TIME_IDENTIFIER}();
const ${RET_IDENTIFIER} = (() => {
    ${userCode}
})();
${REPORT_TIME_IDENTIFIER}();
return ${RET_IDENTIFIER};`;

// compile from TS to JS if requested
if (compileFromTs) {
  const compilationResult = compileTsToJs(machineProgram, []);
  if (compilationResult.compilationErrors.length > 0) {
    console.log(
      JSON.stringify({
        compilation_errors: compilationResult.compilationErrors,
      })
    );
    process.exit(0);
  }
  machineProgram = compilationResult.compiledCode;
}

try {
  const returned = safeVm.run(machineProgram); // run program
  console.log(
    JSON.stringify({
      ...programOutput,
      returned,
      elapsedTimeMs: getElapsedTime(),
    })
  ); // output outcome so Django can collect it
} catch (e) {
  // an error occurred before any test cases could be run
  console.log(JSON.stringify({ execution_error: utils.prettyPrintError(e) }));
}
