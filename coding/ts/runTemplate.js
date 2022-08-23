/**
 * args:
 * templateCode: string
 * envIdentifiers: Record<string, string>
 *
 */
const { VM } = require("vm2");
const assert = require("assert");
const AssertionError = require("assert").AssertionError;
const utils = require("./utils");

const SANDBOX_TIMEOUT = utils.SANDBOX_TIMEOUT;

const templateCode = process.argv[2];
const envIdentifiers = JSON.parse(process.argv[3]); // identifiers for things like AssertionError

const sandboxEnv = {
  // [envIdentifiers.ASSERTION_ERROR_CLASS_ID]: AssertionError,
  [envIdentifiers.PRINT_ERROR_ID]: utils.prettyPrintAssertionError,
  //[envIdentifiers.ASSERT_ID]: assert,
  assert,
};

// instantiation of the vm that'll run the user-submitted program
const safeVm = new VM({
  timeout: SANDBOX_TIMEOUT,
  // TODO see if you can parametrize other things such as memory usage etc.
  sandbox: sandboxEnv,
});

// TODO see if you can parametrize this in order to allow for more output types
try {
  const outcome = safeVm.run(templateCode); // run program
  console.log(JSON.stringify({ tests: outcome })); // output outcome so Django can collect it
} catch (e) {
  // an error occurred before any test cases could be run
  console.log(JSON.stringify({ execution_error: utils.printError(e) }));
}
