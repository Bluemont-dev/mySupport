const lovedOneNarrativeAdd = document.getElementById("lovedOneNarrativeAdd"),
lovedOnesEditDiv = document.getElementById("lovedOnesEditDiv"),
lovedOneNarrativeButtons = document.getElementsByClassName("lovedOneNarrative"),
profile3Selects = document.querySelectorAll("#profileForm3 select"),
lovedOneEditButtons = document.getElementsByClassName("lovedOneNarrativeEdit"),
lovedOneDeleteButtons = document.getElementsByClassName("lovedOneNarrativeDelete"),
profile3SubmitButton = document.getElementById("profile3SubmitButton"),
profile3ResetButton = document.getElementById("profile3ResetButton"),
profile3CancelButton = document.getElementById("profile3CancelButton"),
profile3ActionsDiv = document.getElementById("profile3ActionsDiv");

if (lovedOneNarrativeAdd){
   lovedOneNarrativeAdd.addEventListener("click", function(e) {
        lovedOnesEditDiv.style.display = "inline-block";
        showProfile3CancelButton(true);
        disableNarrativeButtons(true);
    });
}

profile3Selects.forEach(function(element){
    element.addEventListener("change", function(e){
        showProfile3ActionsDiv(true);
    });
});

profile3ResetButton.addEventListener("click", function(e){
    showProfile3ActionsDiv(false);
});

if (profile3CancelButton){
    profile3CancelButton.addEventListener("click", function(e){
        profile3ResetButton.click();
        lovedOnesEditDiv.style.display = "none";
        showProfile3ActionsDiv(false);
        showProfile3CancelButton(false);
        disableNarrativeButtons(false);
    });
}

profile3SubmitButton.addEventListener("click", function(e){
    if (profileForm3.editID.value != ""){
        // set the form to submit to update route, with args. Otherwise, it will submit to regular route to create new row for db
        let urlString = "/profile3/update/" + profileForm3.editID.value
        profileForm3.setAttribute("action", urlString);
    }
    profileForm3.submit();
});

for (var i=0; i < lovedOneEditButtons.length; i++){
    lovedOneEditButtons.item(i).addEventListener("click", function(e){
        loadEditFields(this.id);
    });
}

for (var i=0; i < lovedOneDeleteButtons.length; i++){
    lovedOneDeleteButtons.item(i).addEventListener("click", function(e){
        let URLstring = "/profile3/delete/" + this.id + "/" + profileForm3.formSource3.value;
        if (window.confirm("Are you sure you want to delete this person?")) {
            window.open(URLstring,"_self");
        }
    });
}

function disableNarrativeButtons(disable) {
    for (var i=0; i < lovedOneNarrativeButtons.length; i++){
        if (disable){
            lovedOneNarrativeButtons.item(i).setAttribute("disabled","true");
        }
        else {
            lovedOneNarrativeButtons.item(i).removeAttribute("disabled");
        }
    }
}

function showProfile3ActionsDiv(show){
    if (show){
        profile3ActionsDiv.classList.remove("d-none");
        profile3ActionsDiv.classList.add("d-flex","justify-content-center");
    }
    else {
        profile3ActionsDiv.classList.remove("d-flex","justify-content-center");
        profile3ActionsDiv.classList.add("d-none");
    }
}

function showProfile3CancelButton(show){
    if (show){
        profile3CancelButton.classList.remove("d-none");
        profile3CancelButton.classList.add("d-inline-block");
    }
    else {
        profile3CancelButton.classList.remove("d-inline-block");
        profile3CancelButton.classList.add("d-none");
    }
}

function loadEditFields(editID) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE) {   // XMLHttpRequest.DONE == 4
           if (xmlhttp.status == 200) {
               const editRow = JSON.parse(xmlhttp.responseText);
               const editObject = editRow[0];
                //   iterate thru the editObject and assign each non-null value to the corresponding option in the select inputs
                selectObj = null;
                for (const [key, value] of Object.entries(editObject)) {
                    if (value != null && key != "id"){
                        selectObj = document.getElementById(key);
                        if (key == "challenge"){
                            console.log("We are in the challenge key now.");
                            // we have to iterate through 'challenge' array of values
                            for (j=0; j<selectObj.options.length; j++){
                                if (value.indexOf(selectObj.options[j].text) > -1){
                                    // check whether this select option is in the editRow challenges array
                                    selectObj.options[j].selected = true;
                                }
                            }
                        }
                        else {
                            // no sub-array to traverse, one single value to deal with
                            for (var i = 0; i < selectObj.options.length; i++) {
                                if (selectObj.options[i].text==value) {
                                    selectObj.options[i].selected = true;
                                    // return;
                                }
                            }
                        }
                    }
                }
                // now make these inputs visible, editable by user, etc.
               lovedOneNarrativeAdd.click();
               showProfile3ActionsDiv(true);
                //   update value of hidden field for editID
                profileForm3.editID.value = editID;
           }
           else if (xmlhttp.status == 400) {
              alert('There was an error 400');
           }
           else {
               alert('something else other than 200 was returned');
           }
        }
    };
    ajaxURL = "/profile3/edit/" + editID;
    xmlhttp.open("GET", ajaxURL, true);
    xmlhttp.send();
}

// build array of all selected values from the Challenges pick list
function getSelectValues(select) {
  var result = [];
  var options = select && select.options;
//   re the above line: Basically, the Logical AND operator (&&), will return the value of the second operand if the first is truthy, and it will return the value of the first operand if it is by itself falsy
//  so if we pass this function a select that doesn't exist, "select" is null or false, and therefore "options" is, too. but that would throw an error on the length property in the for loop. Well, anyway . . .
  var opt;
  for (var i=0, iLen=options.length; i<iLen; i++) {
    opt = options[i];

    if (opt.selected) {
      result.push(opt.value || opt.text);
    }
  }
  return result;
}
