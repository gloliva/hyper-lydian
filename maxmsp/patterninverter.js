/*
    Invert or reverse a pattern value list.

    Inspired by the 12-tone technique transformations,
    giving the inversion or retrograde of a pattern.

    Author: gloliva
*/

inlets = 4;
outlets = 2;
autowatch = 1;

// Globals
var sustainList = new Array();
var valueOut = new Array();
var sustainOut = new Array();
var scaleLength = 7;
var updateMode = 0;
var matrixRow = 0;
var restValue = -1;
var maxPatternRange = 15;

// Sustain
var matrixRow = 0;
var full = 0;
var attack = 1;
var sustain = 2;
var release = 3;

// Swapping sustain values for reverse modifier
var envelopeInverseMap = {};
envelopeInverseMap[full] = full;
envelopeInverseMap[attack] =release;
envelopeInverseMap[sustain] = sustain;
envelopeInverseMap[release] = attack;


// set inlet/outlet assist
setinletassist(0, "Sequence Value List");
setinletassist(1, "Sequence Sustain List");
setinletassist(2, "Sequence Update Mode");
setinletassist(3, "Scale Length");

setoutletassist(0, "New Value Sequence");
setoutletassist(1, "New Sustain Sequence");


function msg_int(i) {
    if (inlet == 2) {
        updateMode = i;
    } else if (inlet == 3) {
        scaleLength = i;
    }
}


function list() {
    // Perform sequence modification
    if (inlet == 0) {
        if (sustainList.length <= 0) {
            throw new Error("Sustain List has not been set");
        }

        var valueList = arrayfromargs(arguments);
        if (updateMode == 0) {
            identity(valueList);
        } else if (updateMode == 1) {
            noteReverse(valueList);
        } else if (updateMode == 2) {
            trueReverse(valueList);
        } else if (updateMode == 3) {
            inverse(valueList);
        } else {
            reverseInverse(valueList);
        }
        output();
    // Copy Sustain list
    } else if (inlet == 1) {
        sustainList = new Array();
        for (var i = 0; i < arguments.length; i++) {
            sustainList[i] = arguments[i];
        }
    }
}


function output()
{
    if (sustainOut.length > 0) {
        outlet(1, sustainOut);
    }
    outlet(0, valueOut);
}


function noteReverse(valueList) {
    valueOut = new Array(valueList.length);
    sustainOut = new Array();
    var enabledNotes = new Array();
    var enabledIndexes = new Array();

    // fill with rests
    for (var i = 0; i < valueOut.length; i++) {
        valueOut[i] = restValue;
    }

    for (var i = 0; i < valueList.length; i++) {
        var note = valueList[i];
        if (note >= 0) {
            enabledNotes.push(note);
            enabledIndexes.push(i);
        }
    }

    enabledIndexes.reverse()
    var note;
    var idx;
    for (var i = 0; i < enabledNotes.length; i++) {
        note = enabledNotes[i];
        idx = enabledIndexes[i];

        valueOut[idx] = note;
    }

    // copy over sustain list as is
    for (var i = 0; i < sustainList.length; i++) {
        sustainOut.push(i, matrixRow, sustainList[i]);
    }
}


function trueReverse(valueList) {
    valueOut = new Array(valueList.length);
    sustainOut = new Array();

    // copy over list in reverse
    for (var i = valueList.length - 1; i >= 0; i--) {
        valueOut[i] = valueList[valueList.length - i - 1];
    }

    // copy over sustain in reverse, swapping attack and release values
    var currElem;
    for (var i = sustainList.length - 1; i >= 0; i--) {
        currElem = sustainList[sustainList.length - i - 1];
        sustainOut.push(sustainList.length - i - 1, matrixRow, envelopeInverseMap[currElem]);
    }
}


function identity(valueList) {
    valueOut = new Array(valueList.length);
    sustainOut = new Array();

    // copy over list as is
    for (var i = 0; i < valueList.length; i++){
        valueOut[i] = valueList[i];
    }

    // copy over sustain list as is
    for (var i = 0; i < sustainList.length; i++) {
        sustainOut.push(i, matrixRow, sustainList[i]);
    }
}


function inverse(valueList) {
    // output lists
    valueOut = new Array(valueList.length);
    sustainOut = new Array();

    // lists for handling distance calculations
    distanceList = new Array();
    updatedList = new Array();

    // first distance calculation will always be 0
    distanceList.push(0);
    // updatedList starts the same as valueList
    updatedList.push(valueList[0]);

    var prev = valueList[0];
    var curr = 0;

    // calculate distances between consecutive non-rest notes
    for (var i = 1; i < valueList.length; i++) {
        curr = valueList[i];
        if (curr == -1) {
            // skip values that are -1
            distanceList.push(0);
        } else {
            distanceList.push(prev - curr);
            prev = curr;
        }
    }

    // create updatedList based on distance calculations
    for (var i = 1; i < distanceList.length; i++) {
        if (valueList[i] == -1) {
            // keep rest notes
            updatedList.push(-1);
        } else {
            updatedList.push((updatedList[i - 1] + distanceList[i]) % maxPatternRange);
        }
    }

    // copy updatedList in valueOut
    for (var i = 0; i < updatedList.length; i++) {
        valueOut[i] = updatedList[i];
    }

    // copy over sustain list as is
    for (var i = 0; i < sustainList.length; i++) {
        sustainOut.push(i, matrixRow, sustainList[i]);
    }

    return updatedList;
}


function reverseInverse(valueList) {
    var updatedList = inverse(valueList);
    trueReverse(updatedList);
}
