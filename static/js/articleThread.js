const subject = document.getElementById('subject'),
url = document.getElementById('url'),
title = document.getElementById('title'),
datePublished = document.getElementById('datePublished'),
otherContainer = document.getElementById('otherContainer'),
description = document.getElementById('description'),
useOGImage = document.getElementById('useOGImage'),
ogImathPath = document.getElementById('ogImagePath'),
articleTextPostButton = document.getElementById('articleTextPostButton'),
articleTextCancelButton = document.getElementById('articleTextCancelButton'),
articleURLForm = document.getElementById('articleURLForm'),
articleThreadForm = document.getElementById('articleThreadForm'),
articleID = document.getElementById('articleID'),
textEntryActionButtons = document.getElementById('textEntryActionButtons');

window.addEventListener('load', (event) => {
    if (articleThreadForm.editMode.value == "edit"){
        enablePostButton(true);
        otherContainer.classList.remove('d-none');
        textEntryActionButtons.classList.remove('d-none');
        textEntryActionButtons.classList.add('d-flex');
    }
    if (articleThreadForm.ogImagePath.value != "None" && articleThreadForm.ogImagePath.value != ""){
        ogImageDiv.classList.remove('d-none');
    }
});

url.addEventListener('input', function(){
    // if field is not empty, enable the Go button for ajax call
    if (url.value != ""){
        urlGoButton.removeAttribute('disabled');
    } else {
        urlGoButton.setAttribute('disabled','true');
    }
});

// useOGImage.addEventListener('change', function(){
//     myOGImage = document.querySelector('#ogImageDiv img');
//     if (useOGImage.checked){
//         myOGImage.style.opacity = 1.0;
//     } else {
//         myOGImage.style.opacity = 0.25;
//     }
// });

// description.addEventListener("input", function(){
//     descriptionText.value = description.textContent;
// });

articleTextCancelButton.addEventListener("click",function(){
    if (articleID.value){
        window.open("/article/" + articleID.value,"_self");
    }
    else {
        window.open("/article/thread/","_self");
    }
    
});

articleTextPostButton.addEventListener("click",function(){
    // check required field for title
    if (title.value == ""){
        alert("Please enter a title for the article.");
        return;
    }
    // check required field for datePublished
    if (!isValidDate(datePublished.value)){
        alert("Please enter a valid date when the article was published, in format YYYY-MM-DD");
        return;
    }
    if (articleID.value){
        articleThreadForm.action = "/article/edit/" + articleID.value;
    }
    articleThreadForm.articleURL.value = url.value;
    articleThreadForm.submit();
});


function enablePostButton(myBool){
    if (myBool){
        articleTextPostButton.removeAttribute('disabled');
    } else {
        articleTextPostButton.setAttribute('disabled','true');
    }
}

// async function getArticleDetails(articleURL){
//     articleDetails = await getAPIData('/article/getArticleDetails?url=' + articleURL);
//     return articleDetails;
// }

function checkbox_click(elementID) {
    myOGImage = document.querySelector('#ogImageDiv img');
    if (document.getElementById(elementID).checked){
        myOGImage.style.opacity = 1.0;
    } else {
        myOGImage.style.opacity = 0.25;
    }
}