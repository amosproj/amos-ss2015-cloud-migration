define([
  "require",
  "gew-st-rueck/calc",
  "./testData1.js",
  "./testData2.js",
  "./testData3.js"
], function (
  require,
  calc
) {
  "use strict";

  describe("gew-st-rueck/calc", function () {
    [
      "testData1",
      "testData2",
      "testData3"
    ].forEach(function (dataModule) {
      it("should return the correct result for " + dataModule, function () {
        var testData = require("./" + dataModule + ".js");
        expect(calc(testData.input)).toEqual(testData.expectedOutput);
      });
    });
  });
});
