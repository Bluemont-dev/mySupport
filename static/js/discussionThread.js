const wysiwygButtonsAll = document.querySelectorAll('#wysiwygButtonRow a'),
discussionText = document.getElementById('discussionText'),
rawHTML = document.getElementById('rawHTML'),
subject = document.getElementById('subject'),
discussionTextPostButton = document.getElementById('discussionTextPostButton'),
discussionTextCancelButton = document.getElementById('discussionTextCancelButton'),
discussionThreadForm = document.getElementById('discussionThreadForm'),
discussionID = document.getElementById('discussionID');

let command = "";
let url = "";

discussionText.addEventListener('focus', function(){
    if (discussionText.textContent.trim() == "Enter your discussion text here"){
        discussionText.innerHTML = "";
        // check to see if the "post" button should be enabled
        updatePostButtonStatus();
    } else if (discussionText.textContent == "") {
        updatePostButtonStatus();
    }
});

discussionText.addEventListener('blur', function(){
    updatePostButtonStatus();
    if (discussionText.textContent == ""){
        discussionText.innerHTML = "Enter your discussion text here";
    }
});

window.addEventListener('load', (event) => {
    if (discussionThreadForm.editMode.value == "edit"){
        updatePostButtonStatus();
    }
});

subject.addEventListener('change', function(){
    updatePostButtonStatus();
});

for (var i = 0; i < wysiwygButtonsAll.length; i++){
    wysiwygButtonsAll[i].addEventListener("click", function(){
        command = this.dataset.command;
        // this uses the dataset feature of HTML and grabs the second half of the "data-command" attribute that we assigned to the "a" element, such as "bold"
        if (command == 'createlink' || command == 'insertimage') {
            url = prompt('Enter the link here: ','http:\/\/');
            document.execCommand(command, false, url);
        } else {
            document.execCommand(command, false, null);
        }
    });
}

discussionTextCancelButton.addEventListener("click",function(){
    if (discussionID.value){
        window.open("/discussion/" + discussionID.value,"_self");
    }
    else {
        window.open("/discussion/thread/","_self");
    }
});

discussionTextPostButton.addEventListener("click",function(){
    rawHTML.value = discussionText.innerHTML;
    if (discussionThreadForm.editMode.value == "edit"){
        discussionThreadForm.action = "/discussion/edit/" + discussionThreadForm.discussionID.value;
    }
    discussionThreadForm.submit();
});


function updatePostButtonStatus(){
    if (subject.value != "" && discussionText.textContent.trim() != ""){
        discussionTextPostButton.disabled = false;
    } else {
        discussionTextPostButton.disabled = true;
    }
}
