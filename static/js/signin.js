const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#passwordInput');

window.addEventListener('load', (event) => {
    if (navigator.cookieEnabled == false){
      // cookies are disabled; warn user of lost functionality
      alert("Please enable cookies in your browser. Your registration and log in won't work without this.");
    }
  });

togglePassword.addEventListener('click', function (e) {
    // toggle the type attribute
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    // toggle the eye / eye slash icon
    this.classList.toggle('fa-eye-slash');
    this.classList.toggle('fa-eye');
});