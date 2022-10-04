const getRandomIdentifier = (length) => {
  let result = "";
  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  const charactersLength = characters.length;
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
};

const SANDBOX_TIMEOUT = 1500;

function printError(e) {
  const AssertionError = require("assert").AssertionError;
  if (e instanceof AssertionError) {
    return prettyPrintAssertionError(e);
  }
  return prettyPrintError(e);
}

function prettyPrintError(e) {
  // removes information about the stack of the vm from the error message and only
  // shows the info relevant to the user code
  const tokens = e.stack.split(/(.*)at (new Script(.*))?vm.js:([0-9]+)(.*)/);
  const rawStr = tokens[0]; // error message

  if (rawStr.match(/execution timed out/)) {
    // time out: no other information available
    return `Execution timed out after ${SANDBOX_TIMEOUT} ms`;
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

module.exports = {
  getRandomIdentifier,
  prettyPrintError,
  prettyPrintAssertionError,
  escapeBackTicks,
  SANDBOX_TIMEOUT,
  printError,
};
