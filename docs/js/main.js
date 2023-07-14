jQuery(document).on("keypress", 'form', function(e) {
var code = e.keyCode || e.which;
if (code == 13) {
    e.preventDefault();
    return false;
}
});

let navOpen = false;
function openNav() {
    document.getElementById("main-menu").style.transform = "translateX(0)";
    navOpen = true;
}

function closeNav() {
    document.getElementById("main-menu").style.transform = "translateX(100%)";
    navOpen = false;
}

function toggleNav() {
    navOpen ? closeNav() : openNav();
}

$(document).ready(function(){
    $('#main-figure iframe').attr('src', 'Maps/A - Proposed Zoning.html')

    // Register main menu open/close actions
    $('#top-header, #closeMenuBtn, .openButton').on('click', function(e){
        e.stopPropagation();
        e.preventDefault();
        toggleNav();
    });

    // Handle figure list clicks
    $('#figure-list > li').click(function (){
        // change selected list item
        $('#figure-list > li').not(this).removeClass('selected');
        $(this).addClass('selected');
        // Update iframe url and figure caption
        $('#main-figure > figcaption > h2').text($(this).attr('data-caption'))
        $('#main-figure iframe').attr('src', '') // clear iframe
        $('#main-figure img').attr('src', $(this).attr('data-preview-img'))
    })

    // Handle fullscreen chart clicks
    $('#fullscreen-btn, #main-figure img').on('click', function(){
        // if already full screen; exit
        // else go fullscreen
        if (document.fullscreenElement) {
          document.exitFullscreen();
        } else {
          const currentInteractiveURL = $('#figure-list > li.selected').attr('data-src');
          $('#main-figure iframe').attr('src', currentInteractiveURL);
          $('#main-figure iframe').get(0).requestFullscreen();
        }
      });

});