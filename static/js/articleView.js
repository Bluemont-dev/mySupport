const commentEntryForm = document.getElementById('commentEntryForm'),
commentEditForm = document.getElementById('commentEditForm'),
commentTextContent = document.getElementById('commentTextContent'),
textEntryActionButtons = document.getElementById('textEntryActionButtons'),
commentTextEntryDiv = document.getElementById('commentTextEntryDiv'),
commentTextCancelButton = document.getElementById('commentTextCancelButton'),
commentTextPostButton = document.getElementById('commentTextPostButton'),
commentEditButtons = document.getElementsByClassName('commentEditButton'),
commentDeleteButtons = document.getElementsByClassName('commentDeleteButton'),
commentEditSaveButtons = document.getElementsByClassName('commentEditSaveButton')
commentEditTextContent = document.getElementById('commentEditTextContent');

var actionID = "";
var tempDivString = "";
var tempDivObject = null;
var URLstring = "";

for (var i = 0; i < commentEditButtons.length; i++){
    commentEditButtons[i].addEventListener('click', function(e){
        actionID = parseInt(this.id.replace(/[^0-9\.]/g, ''), 10);
        URLstring = "/article/" + commentEntryForm.articleID.value + "/comment/" + actionID + "/edit#commentItemTextDiv" + actionID;
        window.open(URLstring,"_self");
    });
}

for (var i = 0; i < commentEditButtons.length; i++){
    commentDeleteButtons[i].addEventListener('click', function(e){
        actionID = parseInt(this.id.replace(/[^0-9\.]/g, ''), 10);
        URLstring = "/article/" + commentEntryForm.articleID.value + "/comment/" + actionID + "/delete";
        if (window.confirm("Are you sure you want to delete this comment?")) {
            window.open(URLstring,"_self");
        }
    });
}

for (var i = 0; i < commentEditSaveButtons.length; i++){
    commentEditSaveButtons[i].addEventListener('click', function(e){
        actionID = parseInt(this.id.replace(/[^0-9\.]/g, ''), 10);
        tempDivString = "commentItemTextDiv" + actionID;
        tempDivObject = document.getElementById(tempDivString);
        commentEditTextContent.value = tempDivObject.textContent.trim();
        commentEditForm.submit();
    });
}

if (commentEntryForm){
    // these event listeners only should be added if the user is logged in and has these elements in the DOM

    commentTextEntryDiv.addEventListener('focus', function(){
        if (commentTextEntryDiv.textContent.trim() == "Add a comment ..."){
            commentTextEntryDiv.innerHTML = "";
        }
        displayActionButtons(true);
    });

    commentTextEntryDiv.addEventListener('blur', function(){
        if (commentTextEntryDiv.textContent.trim() == ""){
            commentTextEntryDiv.innerHTML = "Add a comment ...";
            displayActionButtons(false);
        }
    });

    commentTextCancelButton.addEventListener('click', function(){
        commentTextEntryDiv.innerHTML = "Add a comment ...";
        displayActionButtons(false);
    });

    commentTextPostButton.addEventListener('click', function(){
        if (commentTextEntryDiv.textContent.trim() == ""){
            alert("Please add some text to your comment before you send it.");
        } else {
            commentTextContent.value = commentTextEntryDiv.textContent.trim();
            commentEntryForm.submit();
        }
    });

}

function displayActionButtons(display){
    if (display){
        textEntryActionButtons.classList.remove('d-none');
        textEntryActionButtons.classList.add('d-flex');
    } else {
        textEntryActionButtons.classList.remove('d-flex');
        textEntryActionButtons.classList.add('d-none');
    }
}

function articleDeletePrompt(myID){
    // this function is called from an "onclick" reference in the HTML tag of the article delete button
    actionID = parseInt(myID.replace(/[^0-9\.]/g, ''), 10);
    URLstring = "/article/delete/" + actionID;
    if (window.confirm("Are you sure you want to delete this article, and any comments that follow?")) {
        window.open(URLstring,"_self");
    } else {
        return false;
    }
}