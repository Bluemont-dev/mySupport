const zipInput = document.getElementById('zip'),
stateSelect = document.getElementById('state'),
citySelect = document.getElementById('city'),
countySelect = document.getElementById('county'),
peopleGeoActionsDiv = document.getElementById('peopleGeoActionsDiv');

var super4Dict = {};

peopleGeoForm.addEventListener('change', function(e){
    if (e.target.name == "state"){
        // state was changed, so zero out the county and city before submitting
        peopleGeoForm.county.value = "";
        peopleGeoForm.city.value = "";
    }
    peopleGeoForm.submit();
});

window.addEventListener('load', (event) => {
    var getQuery = location.search.substr(1)
    console.log("query is " + getQuery);
    var params = [];
    let queryObject = {}
    params = getQuery.split('&');
    console.log("Params is " + params);
    for (var i=0; i < params.length; i++){
        queryObject[params[i].split("=")[0]] = params[i].split("=")[1];
    }
    console.dir(queryObject)
    // pre-expand the accordions as needed
    if (queryObject.state || queryObject.county || queryObject.city){
        // code here to make the location accordion expand
        document.getElementById('geoButton').click();
        showActionsDiv(true);
    }
    if (queryObject.relationship || queryObject.challenge || queryObject.age || queryObject.gender){
        // code here to make the lovedOnes accordion expand
        document.getElementById('lovedOnesButton').click();
        showActionsDiv(true);
    }
    cityCountyDisableCheck();
    checkForSingles();
});

function checkForSingles() {
    // check to see if any selects have only 1 option other than "choose"; if so, select them
    // note that this might not be needed if we successfully return matches via super4Dict
    if (peopleGeoForm.state.options.length == 2){
        peopleGeoForm.state.options[1].selected = true;
    }
    if (peopleGeoForm.county.options.length == 2){
        peopleGeoForm.county.options[1].selected = true;
    }
    if (peopleGeoForm.city.options.length == 2){
        peopleGeoForm.city.options[1].selected = true;
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
    let latestFormElement = peopleGeoForm.latestSelection.value.split(':')[0];
    console.log("You changed " + latestFormElement + " to " + peopleGeoForm.latestSelection.value.split(':')[1]);
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

// function applyMatches(selectName){
//     let matchedString = "";
//     switch (selectName) {
//       case 'state':
//         if (super4Dict.matches.state.length == 1){
//             matchedString = super4Dict.matches.state[0];
//             for (let i = 0; i < stateSelect.options.length; i++){
//                 if (stateSelect.options[i].text == matchedString){
//                     stateSelect.options[i].selected = true;
//                     break;
//                 }
//             }
//         }
//         break;
//       case 'county':
//         if (super4Dict.matches.county.length == 1){
//             matchedString = super4Dict.matches.county[0];
//             for (let i = 0; i < countySelect.options.length; i++){
//                 if (countySelect.options[i].text == matchedString){
//                     countySelect.options[i].selected = true;
//                     break;
//                 }
//             }
//         }
//         break;
//       case 'city':
//         if (super4Dict.matches.city.length == 1){
//             matchedString = super4Dict.matches.city[0];
//             for (let i = 0; i < citySelect.options.length; i++){
//                 if (citySelect.options[i].text == matchedString){
//                     citySelect.options[i].selected = true;
//                     break;
//                 }
//             }
//         }
//     }
// }

function showActionsDiv(show){
    if (show){
        peopleGeoActionsDiv.classList.remove("d-none");
        peopleGeoActionsDiv.classList.add("d-flex","justify-content-center");

    } else {
        peopleGeoActionsDiv.classList.remove("d-flex","justify-content-center");
        peopleGeoActionsDiv.classList.add("d-none");
    }
}

function getAPIData(url) {
  return new Promise((resolve, reject) => {
    var request = new XMLHttpRequest();
    var errorText = "Sorry, unable to get requested data from the server. For help, please use the Contact Us page.";
    request.open('GET', url, true);
    request.onload = function () {
      if (this.status >= 200 && this.status < 400) {
        // Success!
        var returnedAPIData = JSON.parse(this.response);
        // return data;
        resolve(returnedAPIData);
      } else {
        // We reached our target server, but it returned an error
        reject(errorText);
      }
    };
    request.onerror = function () {
      // There was a connection error of some sort
      reject(errorText);
    };
    request.send();
  });
}

// function clearAllSelects(formID){
//     let selectorString = '#' + formID + " select";
//     allSelects = document.querySelectorAll(selectorString);
//     // for (let i = 0; i < allSelects.length; i++){
//     //     allSelects[i].value="";
//     // }
//     allSelects.forEach(function(item) {
//         item.value = "";
//     });
// }