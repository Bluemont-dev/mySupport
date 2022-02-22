const preload = document.getElementById('preload'),
textEntryAccordion = document.getElementById('textEntryAccordion'),
messageText = document.getElementById('messageText'),
messageThread = document.getElementById('messageThread'),
messagesThreadForm = document.getElementById('messagesThreadForm'),
messageTextCancelButton = document.getElementById('messageTextCancelButton'),
messageTextSendButton = document.getElementById('messageTextSendButton'),
textEntryCollapseButton = document.getElementById('textEntryCollapseButton');

window.addEventListener('load', (event) => {
    if (messagesThreadForm.recipientsCSV.value != ""){
        textEntryAccordion.style.display = "block";
    }
});

messagesThreadForm.name.addEventListener('keyup', async function(e){
    if (messagesThreadForm.name.value != ""){
        preload.style.display = "block";
        preload.innerHTML = "";
        nameRows = await getAPIData('/messages/preload/' + messagesThreadForm.name.value);
        console.log(nameRows)
        let searchString = messagesThreadForm.name.value;
        let regex = new RegExp(searchString, "gi");
        let masterString = "";
        let rawHTML = "";

        if (nameRows.length > 0){
            for (let i = 0; i < nameRows.length; i++){
                masterString = "";
                rawHTML = "";
                if (nameRows[i].first_name != "" && nameRows[i].first_name != null){
                    masterString += nameRows[i].first_name + " ";
                }
                if (nameRows[i].last_name != "" && nameRows[i].last_name != null){
                    masterString += nameRows[i].last_name + " ";
                }
                if (masterString.length > 0){
                    masterString += "/ ";
                }
                masterString += nameRows[i].username;
                masterString = boldAllMatches(masterString, regex);
                rawHTML = `
                <div id=nameID${nameRows[i].id}><a href="#" onclick="addSelectedRecipient(event,${nameRows[i].id})">${masterString}</a></div>
                `;
                // next we need to create a DOM element and append it to the proper div
                newNode = htmlToElement(rawHTML);
                preload.appendChild(newNode);
            }
        } else {
            rawHTML = `
            <div><em>No names found that begin with <strong>${searchString}</strong></em></div>
            `;
            // next we need to create a DOM element and append it to the proper div
            newNode = htmlToElement(rawHTML);
            preload.appendChild(newNode);
        }



    } else {
        preload.style.display = "none";
        console.log("No name in the name field.")
    }

});

recipientNameBadgeXs = document.querySelectorAll('#messageRecipientsList i');

recipientNameBadgeXs.forEach(function(element){
    element.addEventListener("click",  function(e){
        recipientsArray = messagesThreadForm.recipientsCSV.value.split(",");
        for (var i = 0; i < recipientsArray.length; i++){
            if (recipientsArray[i] == element.parentNode.id.substr(8)){
                recipientsArray.splice(i, 1);
            }
        }
        messagesThreadForm.recipientsCSV.value = recipientsArray;
        element.parentNode.remove();
        // use an api call to update the thread, pills, and hidden form element without reloading the page. Unless message text is empty, in which case we reload page
        updateThreadlist();
    });
});

messageText.addEventListener('input',(event) => {
    if (messagesThreadForm.recipientsCSV.value != "" && messageText.value != ""){
        messageTextSendButton.disabled = false;
    } else {
        messageTextSendButton.disabled = true;
    }
});

messageTextCancelButton.addEventListener('click',(event) => {
    messageTextSendButton.disabled = true;
    messageText.value = "";
    textEntryCollapseButton.click();
});

messageTextSendButton.addEventListener('click',(event) => {
    if (messagesThreadForm.recipientsCSV.value != "" && messageText.value != ""){
        messagesThreadForm.submit();
    } else if (messageText.value == "") {
        alert ("Cannot send an empty message. Please type your message into the form.");
    } else {
        alert ("Please select one or more names to receive your message.");
    }
});

function boldAllMatches(masterString, regex) {
  function addBoldTags(match, offset, string) {
    return ("<strong>" + match + "</strong>");
  }
  return masterString.replace(regex, addBoldTags);
}

function addSelectedRecipient(event, id){
    event.preventDefault();
    event.stopPropagation();
    // check to see if selection matches userID
    if (parseInt(id,10) == parseInt(messagesThreadForm.currentUserID.value,10)){
        alert("You can't send a message to yourself. At least not on this website.");
        return;
    }
    // check to see if selected name is already in recipients list
    if (messagesThreadForm.recipientsCSV.value.includes(id)){
        alert("That person is already in your list of recipients for this message.");
        return;
    }
    // add the selected name to recipientsCSV and reload page
    if (messagesThreadForm.recipientsCSV.value != ""){
        messagesThreadForm.recipientsCSV.value += "," + id;
    } else {
        messagesThreadForm.recipientsCSV.value += id;
    }
    updateThreadlist();
}

async function updateThreadlist() {
    if (messageText.value == ""){
        window.open("/messages/thread/" + messagesThreadForm.recipientsCSV.value,"_self");
    } else {
        if (messagesThreadForm.recipientsCSV.value != ""){
            // update the threads shown, based on newly updated recipients list
            threadRows = await getAPIData('ajax,' + messagesThreadForm.recipientsCSV.value);
            // console.log("After the API call, the value of threadRows is " + JSON.stringify(threadRows));
            // zero out messages thread; replace it with the new content from threadRows
            messageThread.innerHTML = "";
            newHTML = "";
            for (var i = 0; i < threadRows.length; i++) {
                var obj = threadRows[i];
                console.log("Display name is " + obj.displayName);
                newHTML +=
                `
                <div class="row mb-1 p-1 {{ loop.cycle('odd', 'even') }}">
                    <div  class="thumbnailDiv col-md-auto mx-auto d-flex justify-content-left">
                        <img class = "thumbnailImage" alt=${obj.displayName} src="/static/avatars/${obj.profileImage}">
                    </div>
                    <div class="col">
                        <p><strong>${obj.displayName}</strong> / <small>${obj.dateTimeString}</small></p>
                        <p>${obj.text}</p>
                    </div>
                </div>

                `
            }
            messageThread.innerHTML = newHTML;
        } else {
            // nobody remains in recipient list, so zero out the threads shown
            messageThread.innerHTML = "";
        }
    }
}