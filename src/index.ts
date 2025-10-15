import $ from 'jquery';
import { get_next_pair } from './connector';

$("#button_left").on("click", function() {
  $(".button_navigation").removeClass("button_selected")
  $(this).addClass("button_selected")
  $("#button_next").removeAttr("disabled")
})
$("#button_right").on("click", function() {
  $(".button_navigation").removeClass("button_selected")
  $(this).addClass("button_selected")
  $("#button_next").removeAttr("disabled")
})
$("#button_bothgood").on("click", function() {
  $(".button_navigation").removeClass("button_selected")
  $(this).addClass("button_selected")
  $("#button_next").removeAttr("disabled")
})
$("#button_bothbad").on("click", function() {
  $(".button_navigation").removeClass("button_selected")
  $(this).addClass("button_selected")
  $("#button_next").removeAttr("disabled")
})

$(document).on('keypress', function (e) {
  if (e.key === 'e' || e.key === 'E')
    $("#button_left").trigger("click")
  if (e.key === 'r' || e.key === 'R')
    $("#button_right").trigger("click")
  if (e.key === 'd' || e.key === 'D')
    $("#button_bothbad").trigger("click")
  if (e.key === 'f' || e.key === 'F')
    $("#button_bothgood").trigger("click")
  if (e.key === 'n' || e.key === 'N')
    $("#button_next").trigger("click")
});

$("#toggle_differences").on("change", function() {
  if ($(this).is(":checked")) {
    $(".difference").removeClass("hidden")
  } else {
    $(".difference").addClass("hidden")
  }
})


function load_next() {
  let data = get_next_pair()

  let html_new = ""
  for (let i = 0; i < data.src.length; i++) {
    html_new += `
    <div class="output">${data.out_a[i]}</div>
    <div class="output">${data.src[i]}</div>
    <div class="output">${data.out_b[i]}</div>
    <br>
    <br>
    `
  }
  console.log(html_new)
  $("#output_div").html(html_new)

  console.log($("#output_div"))
}

$("#button_next").attr("disabled", "disabled")

$("#button_next").on("click", function() {
  load_next()
})

load_next()