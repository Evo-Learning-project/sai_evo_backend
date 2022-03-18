/*
usage: 
node runWithAssertions.js programCode assertions
arguments:
programCode is a STRING containing a js program
assertions is an ARRAY of strings representing assertions made using node assertions
output: 
an array printed to the console (and collected by Django via subprocess.check_output()) where each
entry corresponds to an assertion and is an object:
{ 
    id: Number,
    assertion: String,
    public: Boolean,
    passed: Boolean,
    error: String,
} 
where id is the id of the assertion (as in the Django database),
assertion is the string containing the assertion verbatim,
public indicates whether the assertion is to be shown to the user or it's secret,
passed represents the outcome of running the assertion on the program,
and error is only present if the assertion failed
*/

// The VM2 module allows execution of arbitrary code safely using
// a sandboxed, secure virtual machine
const { VM } = require("vm2");
const assert = require("assert");
const ts = require("typescript");
const AssertionError = require("assert").AssertionError;
const timeout = 1000;
const tsConfig = require("./tsconfig.json");

const getRandomIdentifier = (length) => {
  let result = "";
  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  const charactersLength = characters.length;
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
};

function tsCompile(source, options = null) {
  // Default options -- you could also perform a merge, or use the project tsconfig.json
  if (null === options) {
    options = { compilerOptions: { module: ts.ModuleKind.CommonJS } };
  }
  return ts.transpileModule(source, options).outputText;
}

// instantiation of the vm that'll run the user-submitted program
const safeVm = new VM({
  timeout, // set timeout to prevent endless loops from running forever
  sandbox: {
    prettyPrintError,
    prettyPrintAssertionError,
    assert,
    AssertionError,
  },
});

function prettyPrintError(e) {
  // removes information about the stack of the vm from the error message and only
  // shows the info relevant to the user code
  const tokens = e.stack.split(/(.*)at (new Script(.*))?vm.js:([0-9]+)(.*)/);
  const rawStr = tokens[0]; // error message

  if (rawStr.match(/execution timed out/)) {
    // time out: no other information available
    return `Execution timed out after ${timeout} ms`;
  }

  const formattedStr = rawStr.replace(
    /(.*)vm.js:([0-9]+):?([0-9]+)?(.*)/g,
    function (_a, _b, c, d) {
      // actual line of the error is one less than what's detected due to an
      // additional line of code injected in the vm (hence the -1)
      return `on line ${parseInt(c) - 1}` + (d ? `, at position ${d})` : "");
    }
  );
  return formattedStr;
}

// does the same as prettyPrintError(), but it's specifically designed to work with AssertionErrors
function prettyPrintAssertionError(e) {
  const expected = e.expected;
  const actual = e.actual;
  const [errMsg, _] = e.stack.split("\n");
  return (
    errMsg +
    " expected value " +
    JSON.stringify(expected) +
    ", but got " +
    JSON.stringify(actual)
  );
}

const escapeBackTicks = (t) => t.replace(/`/g, "\\`");

const userCode = tsCompile(process.argv[2], tsConfig);

const assertions = JSON.parse(process.argv[3]);

const outputArrIdentifier = getRandomIdentifier(20);

// turn array of strings representing assertions to a series of try-catch blocks
//  where those assertions are evaluated and the result is pushed to an array
// the resulting string will be inlined into the program that the vm will run
// TODO generate random identifier for 'ran' object!!
const assertionString = assertions
  .map(
    (a) =>
      `
        ran = {
            id: \`${a.id}\`,
        }
        try {
            // run the assertion

            ${a.assertion}

            ran.passed = true // if no exception is thrown, the test case passed
        } catch(e) {
            ran.passed = false
            if(e instanceof AssertionError) {
                //ran.error = userCode
                ran.error = prettyPrintAssertionError(e) // test case failed but cose threw no errors
            } else {
                ran.error = prettyPrintError(e) // code threw an error during test case execution
            }
        }
        ${outputArrIdentifier}[${outputArrIdentifier}.length] = ran // push test case results
    `
  )
  .reduce((a, b) => a + b, ""); // reduce array of strings to a string

const runnableProgram = `const ${outputArrIdentifier} = [];
${userCode}
// USER CODE ENDS HERE
if(Object.isFrozen(${outputArrIdentifier})) {
    // abort if user intentionally froze the output array
    throw new Error("Internal error")
}
// inline assertions
${assertionString}
// output outcome object to console
${outputArrIdentifier}`;

try {
  const outcome = safeVm.run(runnableProgram); // run program
  console.log(JSON.stringify({ tests: outcome })); // output outcome so Django can collect it
} catch (e) {
  // an error occurred before any test cases could be ran
  console.log(JSON.stringify({ error: prettyPrintError(e) }));
}
