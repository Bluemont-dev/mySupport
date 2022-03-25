const form  = document.getElementsByTagName('form')[0];

let clientSideFeedback = document.getElementById('clientSideFeedback');

window.addEventListener('load', (event) => {
  if (navigator.cookieEnabled == false){
    // cookies are disabled; warn user of lost functionality
    alert("Please enable cookies in your browser. Your registration and log in won't work without this.");
  }
});

form.addEventListener('submit', function (event) {
  // if the fields are valid, we let the form submit
  //zero out the variables and DOM items
  clientSideFeedback.textContent = "";
  clientSideFeedback.classList.remove('alert-danger');
  let passwordString = document.getElementById('passwordInput').value;
  let errorText = "";
  let checkChar = "";
  let hasALower = false;
  let hasAnUpper = false;
  let hasADigit = false;
  // check password for minimun length of 8 characters
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

  if(errorText != "") {
    // If we have error text, we display an appropriate error message
    showError(errorText);
    // Then we prevent the form from being sent by canceling the event
    event.preventDefault();
  }

});

const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#passwordInput');

togglePassword.addEventListener('click', function (e) {
    // toggle the type attribute
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    // toggle the eye / eye slash icon
    this.classList.toggle('fa-eye-slash');
    this.classList.toggle('fa-eye');
});

function showError(errorText) {
  clientSideFeedback.textContent = errorText;
  clientSideFeedback.classList.add('alert-danger');
}