function getAPIData(url) {
  return new Promise((resolve, reject) => {
    var request = new XMLHttpRequest();
    var errorText = "Sorry, unable to get requested data from the server. Please notify Bluemont.";
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

function htmlToElement(html) {
  var template = document.createElement('template');
  html = html.trim(); // Never return a text node of whitespace as the result
  template.innerHTML = html;
  // return template.content.firstChild;
  newNode = template.content.firstChild;
  // newNode = htmlToElement(newHTML);
  return newNode;
}

function isValidDate(dateString) {
    // First check for the pattern YYYY-MM-DD
    if(!/^\d{4}-\d{1,2}-\d{1,2}$/.test(dateString))
        return false;

    // Parse the date parts to integers
    var parts = dateString.split("-");
    var day = parseInt(parts[2], 10);
    var month = parseInt(parts[1], 10);
    var year = parseInt(parts[0], 10);

    // Check the ranges of month and year
    if(year < 1000 || year > 3000 || month == 0 || month > 12)
        return false;

    var monthLength = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ];

    // Adjust for leap years
    if(year % 400 == 0 || (year % 100 != 0 && year % 4 == 0))
        monthLength[1] = 29;

    // Check the range of the day
    return day > 0 && day <= monthLength[month - 1];
}