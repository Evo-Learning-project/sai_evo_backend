// const ts = require("typescript");

// const getRandomIdentifier = (length) => {
//   let result = "";
//   const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
//   const charactersLength = characters.length;
//   for (let i = 0; i < length; i++) {
//     result += characters.charAt(Math.floor(Math.random() * charactersLength));
//   }
//   return result;
// };

// function tsCompile(source, options = null) {
//   // Default options -- you could also perform a merge, or use the project tsconfig.json
//   if (null === options) {
//     options = { compilerOptions: { module: ts.ModuleKind.CommonJS } };
//   }
//   return ts.transpileModule(source, options).outputText;
// }
