// The VM2 module allows execution of arbitrary code safely using
// a sandboxed, secure virtual machine
const { VM } = require("vm2");
const assert = require("assert");
const AssertionError = require("assert").AssertionError;
const compileTsToJs = require("./tsCompilation").tsToJs;
const utils = require("./utils");

// rename assert and AssertionError inside generated program to make them inaccessible to user
const assertIdentifier = utils.getRandomIdentifier(20);
const assertionErrorIdentifier = utils.getRandomIdentifier(20);
const prettyPrintErrorIdentifier = utils.getRandomIdentifier(20);
const prettyPrintAssertionErrorIdentifier = utils.getRandomIdentifier(20);

const SANDBOX_TIMEOUT = utils.SANDBOX_TIMEOUT;

// instantiation of the vm that'll run the user-submitted program
const safeVm = new VM({
  timeout: SANDBOX_TIMEOUT, // set timeout to prevent endless loops from running forever
  sandbox: {
    [prettyPrintErrorIdentifier]: utils.prettyPrintError,
    [prettyPrintAssertionErrorIdentifier]: utils.prettyPrintAssertionError,
    [assertIdentifier]: assert,
    [assertionErrorIdentifier]: AssertionError,
  },
});

const compileFromTs = JSON.parse(process.argv[4] ?? "false");

const testcases = JSON.parse(process.argv[3]);

const outputArrIdentifier = utils.getRandomIdentifier(32);
const testDetailsObjIdentifier = utils.getRandomIdentifier(32);
const testcaseCounterIdentifier = utils.getRandomIdentifier(32);

const vmIdentifiers = [
  // outputArrIdentifier,
  //testDetailsObjIdentifier,
  //testcaseCounterIdentifier,
  assertIdentifier,
  assertionErrorIdentifier,
  prettyPrintErrorIdentifier,
  prettyPrintAssertionErrorIdentifier,
];

// turn array of strings representing assertions to a series of try-catch blocks
//  where those assertions are evaluated and the result is pushed to an array
// the resulting string will be inlined into the program that the vm will run
const assertionString =
  `let ${testcaseCounterIdentifier} = 0;` +
  testcases
    .map(
      (a) =>
        `
        var ${testDetailsObjIdentifier}${compileFromTs ? ":any" : ""} = {
            id: \`${a.id}\`,
        }
        try {
            // run the assertion

            ${a.assertion.replace(/assert/g, assertIdentifier)}

            ${testDetailsObjIdentifier}.passed = true // if no exception is thrown, the test case passed
        } catch(e) {
            ${testDetailsObjIdentifier}.passed = false
            if(e instanceof ${assertionErrorIdentifier}) {
                ${testDetailsObjIdentifier}.error = ${prettyPrintAssertionErrorIdentifier}(e) // test case failed but code threw no errors
            } else {
                ${testDetailsObjIdentifier}.error = ${prettyPrintErrorIdentifier}(e) // code threw an error during test case execution
            }
        }
        ${outputArrIdentifier}[${testcaseCounterIdentifier}++] = ${testDetailsObjIdentifier} // push test case results
    `
    )
    .join("");

const userCode = process.argv[2];

let machineProgram = `const ${outputArrIdentifier}${
  compileFromTs ? ":any" : ""
} = [];
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

if (compileFromTs) {
  const compilationResult = compileTsToJs(machineProgram, vmIdentifiers);
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
  const outcome = safeVm.run(machineProgram); // run program
  console.log(JSON.stringify({ tests: outcome })); // output outcome so Django can collect it
} catch (e) {
  // an error occurred before any test cases could be run
  console.log(JSON.stringify({ execution_error: utils.prettyPrintError(e) }));
}
