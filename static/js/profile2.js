const usernameInput = document.getElementById("username"),
firstNameInput = document.getElementById("firstNameInput"),
lastNameInput = document.getElementById("lastNameInput"),
displayNameOptionUsername = document.getElementById("displayNameOptionUsername"),
displayNameOptionFirstLast = document.getElementById("displayNameOptionFirstLast"),
fileElem = document.getElementById("fileElem"),
thumbnailDiv = document.getElementById("thumbnailDiv"),
dbThumbnailImage = document.getElementById("thumbnailImage"),
useOrCancel = document.getElementById("useOrCancel"),
fileSelectDiv = document.getElementById("fileSelectDiv"),
fileSelectUse = document.getElementById("fileSelectUse"),
fileSelectCancel = document.getElementById("fileSelectCancel"),
thumbnailSaveStatus = document.getElementById("thumbnailSaveStatus"),
profile2SubmitButton = document.getElementById("profile2SubmitButton");


var radios = document.profileForm2.display_name_option;
for (var i = 0; i < radios.length; i++) {
    radios[i].addEventListener('change', function() {
      // code goes here for both radio buttons
      updateThumbnailFigcaption();
    });
}

usernameInput.addEventListener("change", function(e) {
  updateThumbnailFigcaption();
  if (usernameInput.value==""){
    alert("Username is required. Please enter a username.");
    usernameInput.click();
    return
  }
}, false);

let nameInputs = [firstNameInput, lastNameInput];
nameInputs.forEach(function(element) {
  element.addEventListener("change", function() {
      if (firstNameInput.value=="" && lastNameInput.value==""){
        // disable the second radio button
        displayNameOptionFirstLast.disabled = true;
        // if firstLast is checked, switch to username
        if (displayNameOptionFirstLast.checked) {
          displayNameOptionFirstLast.checked = false;
          displayNameOptionUsername.checked = true;
        }
      }
      else {
        // if firstlast is disabled, enable it
          if (displayNameOptionFirstLast.disabled == true) {
            displayNameOptionFirstLast.disabled = false;
          }
      }
      updateThumbnailFigcaption();
  }, false);
});

window.addEventListener('load', (event) => {
    if (firstNameInput.value=="" && lastNameInput.value==""){
      // disable the second radio button
      displayNameOptionFirstLast.disabled = true;
    }
});

function updateThumbnailFigcaption() {
  let username = document.profileForm2.username.value;
  let firstName = document.profileForm2.first_name.value;
  let lastName = document.profileForm2.last_name.value;
  let displayName = "";
  let displayNameOptionNumber = 0;
  let displayNameMaxLength = 20;
  if (displayNameOptionFirstLast.checked) {
    displayNameOptionNumber = 2;
  }
  else {
    displayNameOptionNumber = 1;
  }
  if (displayNameOptionNumber == 1) {
    // we're using username as displayname
    displayName = username;
    // truncate the string to maxlength w/ellipsis if needed
    if (displayName.length > displayNameMaxLength){
      displayName = displayName.substring(0, 16) + "...";
    }
  }
  else {
    // we're using firstname and lastname as the displayname
    if (firstName.length + lastName.length < displayNameMaxLength){
      // no shortening needed
      displayName = firstName + " " + lastName;
    }
    else {
      // too long, must shorten
      if (firstName.length < displayNameMaxLength - 2){
        displayName = firstName + " " + lastName.substr(0,1);
      }
      else {
        displayName = firstName.substr(0,displayNameMaxLength-2) + " " + lastName.substr(0,1);
      }
    }
  }
  document.getElementById("thumbnailFigcaption").textContent = displayName;
}

fileElem.addEventListener("change", handleFiles, false);

function handleFiles() {
  if (this.files.length) {
    var thumbnailFigcaption = document.getElementById("thumbnailFigcaption");
    let blob = document.querySelector("#thumbnailFigure img");
    thumbnailFigure.removeChild(blob);
    const img = document.createElement("img");
    img.src = URL.createObjectURL(this.files[0]);
    // img.height = 60;
    img.onload = function() {
      URL.revokeObjectURL(this.src); //even without this function, the upload fails
    };
    thumbnailFigure.insertBefore(img, thumbnailFigcaption);
    fileSelectDiv.classList.remove("d-flex");
    fileSelectDiv.classList.add("d-none");
    useOrCancel.classList.remove("d-none");
    userOrCancel.classList.add("d-flex");
    thumbnailSaveStatus.style.display = "none";
  }
}

fileSelectUse.addEventListener("click", function(e) {
  fileSelectDiv.classList.add("d-flex");
  fileSelectDiv.classList.remove("d-none");
  useOrCancel.classList.add("d-none");
  userOrCancel.classList.remove("d-flex");
  thumbnailSaveStatus.style.display = "inline-block";
  e.preventDefault(); // prevent navigation to "#"
}, false);

fileSelectCancel.addEventListener("click", function(e) {
  // remove blob, restore db thumbnail, both as first child of thumbnailFigure
  let blob = document.querySelector("#thumbnailFigure img");
  thumbnailFigure.removeChild(blob);
  thumbnailFigure.insertBefore(dbThumbnailImage, thumbnailFigcaption);
  fileSelectDiv.classList.add("d-flex");
  fileSelectDiv.classList.remove("d-none");
  useOrCancel.classList.add("d-none");
  useOrCancel.classList.remove("d-flex");
  // reset the file select element to empty
  document.getElementById("fileElem").value = "";
  e.preventDefault(); // prevent navigation to "#"
}, false);

profile2SubmitButton.addEventListener("click", function(e) {
  // code goes here to build URL string and submit the form data
  if (usernameInput.value==""){
    alert("Username is required. Please enter a username.");
    usernameInput.click();
    return
  }
  let displayNameOption = 0;
  if (profileForm2.displayNameOptionUsername.checked){
    displayNameOption = 1;
  }
  else {
    displayNameOption= 2;
  }
  let argstring = `username=${profileForm2.username.value}&first_name=${profileForm2.first_name.value}&last_name=${profileForm2.last_name.value}&display_name_option=${displayNameOption}`;
  profileForm2.setAttribute("action","/profile2?" + argstring);
  profileForm2.submit();
}, false);