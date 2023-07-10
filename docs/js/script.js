jQuery(document).on("keypress", 'form', function(e) {
  var code = e.keyCode || e.which;
  if (code == 13) {
    e.preventDefault();
    return false;
  }
});

function openNav() {
  document.getElementById("menu").style.transform = "translateX(0)";
  console.log("open");
}

function closeNav() {
  document.getElementById("menu").style.transform = "translateX(100%)";
}

var selected_mode = "land_values_per_m2";

function set_initial_selected(mode) {
  selected_mode = mode;
  console.log("Set initial presets");

}

function swapMap() {
  //$('#main-title').text("Travel time to " + selected_destination + " by " + selected_mode);
  var path = selected_mode + ".html";
  console.log(path);
  $(".map").each(function(i) {
    if ($(this).attr('src') == path) {
      $(this).css("display", "block");
    } else {
      $(this).css("display", "none");
    }
  });

}

function update(sel) {
  console.log("Processing");


  $(".mode").css("background-color", "#ebebeb");
  $('.mode').attr("aria-pressed", "false");
  $(sel).css("background-color", "#c4c4c4");
  $('.mode').attr("aria-pressed", "true");
  
  if ($(sel).text() == "Land Values") {
  selected_mode = "land_values_per_m2";
  //change h1 with id chart-title to "Land Values"
  $('#chart_title').text("Oak Bay Land Values per M2");
}
else {
  selected_mode = "total_values_per_m2";
  //change h1 with id chart-title to "Total Values"
  $('#chart_title').text("Oak Bay Total (Land + Improvement) Values per M2");
}
  swapMap();


}

$('.destination').first().css("background-color", "#c4c4c4");
$('.mode').first().css("background-color", "#c4c4c4");
$('.map').first().css("display", "block");
