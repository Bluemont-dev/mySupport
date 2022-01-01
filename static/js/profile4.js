const zipInput = document.getElementById('zip'),
stateSelect = document.getElementById('state'),
citySelect = document.getElementById('city'),
countySelect = document.getElementById('county'),
profile4ActionsDiv = document.getElementById('profile4ActionsDiv'),
profile4SubmitButton = document.getElementById('profile4SubmitButton');

var super4Dict = {};

profileForm4.addEventListener('change', async function(e){
    let ajaxURL = "";
    profileForm4.latestSelection.value = e.target.name + ':' + e.target.value;
    showActionsDiv(true);
    if (e.target.name == "zip"){
        if (zipInput.value == ""){
            return;
        } else {
            // send the zip code for validation
            ajaxURL = "profile4/geo?&zip=" + e.target.value;
            super4Dict = await getAPIData(ajaxURL);
            // console.log("After the THEN block, the value of super4Dict is " + JSON.stringify(super4Dict));
            // if zip is invalid
            if (super4Dict.hasOwnProperty('selects') && super4Dict.selects.zip[0] == 'invalid'){
                alert("You provided a ZIP code that is not in our database. Please try again, or skip it and select your state, city and county.");
                return;
            }
            returnRows(super4Dict);
        }
    } else if (e.target.name == "state"){
        // if value is empty, do a reset of the form
        if (stateSelect.value == ""){
            profileForm4.reset();
        } else {
            ajaxURL = "profile4/geo?";
            // the code below assumes blue-sky change to the state, ignore zip code. But if we're choosing among fewer than 50 states, we need to reconcile both state and zip.
            if (stateSelect.options.length < 51){
                ajaxURL += "&state=" + e.target.value;
                ajaxURL += "&zip=" + zipInput.value;
                super4Dict = await getAPIData(ajaxURL);
                console.log("After the THEN block, the value of super4Dict is " + JSON.stringify(super4Dict));
                returnRows(super4Dict);
            } else {
                // we have a selection for state, so submit it and zipcode to the API
                ajaxURL += "&state=" + e.target.value;
                super4Dict = await getAPIData(ajaxURL);
                console.log("After the THEN block, the value of super4Dict is " + JSON.stringify(super4Dict));
                returnRows(super4Dict);
            }
        }
    } else if (e.target.name == "county"){
        // we can assume a state has been selected already, so submit the state and county to get the updated cities list
            ajaxURL = "profile4/geo?";
            ajaxURL += "&state=" + stateSelect.value;
            ajaxURL += "&county=" + e.target.value;
            super4Dict = await getAPIData(ajaxURL);
            console.log("After the THEN block, the value of super4Dict is " + JSON.stringify(super4Dict));
            returnRows(super4Dict);
    } else {
        // it must have been "city" that changed
        // we can assume a state has been selected already, so submit the state and city to get the updated counties list
            ajaxURL = "profile4/geo?";
            ajaxURL += "&state=" + stateSelect.value;
            ajaxURL += "&city=" + e.target.value;
            super4Dict = await getAPIData(ajaxURL);
            console.log("After the THEN block, the value of super4Dict is " + JSON.stringify(super4Dict));
            returnRows(super4Dict);
    }
    // also resolve unchosen states, in cases where a zipcode covers more than one state
    if (super4Dict.matches.state.length > 1){
        disableSubmitButton(true);
        alert("Please select a state.");
    } else {
        disableSubmitButton(false);
    }
});

profileForm4.addEventListener('reset', function(e){
    disableSubmitButton(false);
    profileForm4.reset();
});

window.addEventListener('load', (event) => {
    cityCountyDisableCheck();
    checkForSingles();
});

function checkForSingles() {
    // check to see if any selects have only 1 option other than "choose"; if so, select them
    // note that this might not be needed if we successfully return matches via super4Dict
    if (profileForm4.state.options.length == 2){
        profileForm4.state.options[1].selected = true;
    }
    if (profileForm4.county.options.length == 2){
        profileForm4.county.options[1].selected = true;
    }
    if (profileForm4.city.options.length == 2){
        profileForm4.city.options[1].selected = true;
    }
}

function cityCountyDisableCheck(){
    //   check whether any state is selected; if not, disable cities and counties pick lists, and vice versa
    if (stateSelect.value == ""){
        citySelect.disabled = true;
        countySelect.disabled = true;
    }
    else {
        citySelect.removeAttribute('disabled');
        countySelect.removeAttribute('disabled');
    }
}

function returnRows(super4Dict){
    // check to see which input was the last one selected; substring before the colon. e.g. 'zip:abc
    let latestFormElement = profileForm4.latestSelection.value.split(':')[0];
    console.log("You changed " + latestFormElement + " to " + profileForm4.latestSelection.value.split(':')[1]);
    // for all the other selects, delete their contents, and rebuild them with the values returned in "selects"
    if (latestFormElement != 'state'){
        deleteSelectOptions(stateSelect);
        rebuildSelectOptions(stateSelect, super4Dict.selects.state);
        applyMatches('state');
    }
    if (latestFormElement != 'county'){
        deleteSelectOptions(countySelect);
        rebuildSelectOptions(countySelect, super4Dict.selects.county);
        applyMatches('county');
    }
    if (latestFormElement != 'city'){
        deleteSelectOptions(citySelect);
        rebuildSelectOptions(citySelect, super4Dict.selects.city);
        applyMatches('city');
    }
    cityCountyDisableCheck();
}

function deleteSelectOptions(select){
    for (i = select.options.length-1; i > 0; i--){
        select.options[i].remove();
    }
}

function rebuildSelectOptions(select, list){
    for (i = 0; i < list.length; i++){
        const newOption = document.createElement("option");
        newOption.textContent = list[i];
        select.appendChild(newOption);
    }
}

function applyMatches(selectName){
    let matchedString = "";
    switch (selectName) {
      case 'state':
        if (super4Dict.matches.state.length == 1){
            matchedString = super4Dict.matches.state[0];
            for (let i = 0; i < stateSelect.options.length; i++){
                if (stateSelect.options[i].text == matchedString){
                    stateSelect.options[i].selected = true;
                    break;
                }
            }
        }
        break;
      case 'county':
        if (super4Dict.matches.county.length == 1){
            matchedString = super4Dict.matches.county[0];
            for (let i = 0; i < countySelect.options.length; i++){
                if (countySelect.options[i].text == matchedString){
                    countySelect.options[i].selected = true;
                    break;
                }
            }
        }
        break;
      case 'city':
        if (super4Dict.matches.city.length == 1){
            matchedString = super4Dict.matches.city[0];
            for (let i = 0; i < citySelect.options.length; i++){
                if (citySelect.options[i].text == matchedString){
                    citySelect.options[i].selected = true;
                    break;
                }
            }
        }
    }
}

function showActionsDiv(show){
    if (show){
        profile4ActionsDiv.classList.remove("d-none");
        profile4ActionsDiv.classList.add("d-flex","justify-content-center");

    } else {
        profile4ActionsDiv.classList.remove("d-flex","justify-content-center");
        profile4ActionsDiv.classList.add("d-none");
    }
}

function disableSubmitButton(disable){
    if (disable){
        profile4SubmitButton.disabled = true;
    } else {
        profile4SubmitButton.removeAttribute('disabled');
    }
}

// function getAPIData(url) {
//   return new Promise((resolve, reject) => {
//     var request = new XMLHttpRequest();
//     var errorText = "Sorry, unable to get requested data from the server. Please notify Bluemont.";
//     request.open('GET', url, true);
//     request.onload = function () {
//       if (this.status >= 200 && this.status < 400) {
//         // Success!
//         var returnedAPIData = JSON.parse(this.response);
//         // return data;
//         resolve(returnedAPIData);
//       } else {
//         // We reached our target server, but it returned an error
//         reject(errorText);
//       }
//     };
//     request.onerror = function () {
//       // There was a connection error of some sort
//       reject(errorText);
//     };
//     request.send();
//   });
// }