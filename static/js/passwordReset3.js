const form  = document.getElementsByTagName('form')[0];
const togglePassword = document.querySelector('#togglePassword');
const password1 = document.getElementById('passwordInput1');
const password2 = document.getElementById('passwordInput2');

let clientSideFeedback = document.getElementById('clientSideFeedback');

window.addEventListener('load', (event) => {
  // get token from URL and store in hidden field
  let urlString = window.location.href;
  let urlArray = urlString.split('/');
  let token = urlArray[urlArray.length-1];
  form.token.value = token;
  // update form action to include this token
  form.action += "/" + token;
});

togglePassword.addEventListener('click', function (e) {
  // toggle the type attribute for both password inputs
  const type1 = password1.getAttribute('type') === 'password' ? 'text' : 'password';
  password1.setAttribute('type', type1);
  const type2 = password2.getAttribute('type') === 'password' ? 'text' : 'password';
  password2.setAttribute('type', type2);
  // toggle the eye / eye slash icon
  this.classList.toggle('fa-eye-slash');
  this.classList.toggle('fa-eye');
});

form.addEventListener('submit', function (event) {
  // if the fields are valid, we let the form submit
  //zero out the variables and DOM items
  clientSideFeedback.textContent = "";
  clientSideFeedback.classList.remove('alert-danger');
  let passwordString = password1.value;
  let passwordString2 = password2.value;
  let errorText = "";
  let checkChar = "";
  let hasALower = false;
  let hasAnUpper = false;
  let hasADigit = false;
  // check password for minimum length of 8 characters
  if(passwordString.length < 8) {
    errorText += "Password must be at least 8 characters.\n";
  }
  //loop thru the string and check for the required items
  for (let i = 0; i<passwordString.length; i++) {
    checkChar = passwordString.charAt(i);
     if (!isNaN(checkChar * 1)) {
       hasADigit = true;
     }
  }
  if (passwordString != passwordString.toUpperCase()) {
    hasALower = true;
  }
  if (passwordString != passwordString.toLowerCase()) {
    hasAnUpper = true;
  }
  // check password for at least 1 lowercase char
  if(!hasALower) {
    errorText += "Password must have at least 1 lowercase letter.\n";
  }
  // check for at least 1 uppercase char
  if(!hasAnUpper) {
    errorText += "Password must have at least 1 uppercase letter.\n";
  }
  // check for at least 1 digit
  if(!hasADigit) {
    errorText += "Password must have at least 1 digit.\n";
  }
  // check to ensure passwords match
  if (passwordString != passwordString2){
    errorText += "Passwords must match.\n";
  }
  if(errorText != "") {
    // If we have error text, we display an appropriate error message
    showError(errorText);
    // Then we prevent the form from being sent by canceling the event
    event.preventDefault();
  }

});

function showError(errorText) {
  clientSideFeedback.textContent = errorText;
  clientSideFeedback.classList.add('alert-danger');
}