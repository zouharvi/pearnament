import $ from 'jquery';
import { get_next_pair, Item } from './connector';
let response_log: Array<string> = []

$("#toggle_differences").on("change", function() {
  if ($(this).is(":checked")) {
    $(".difference").removeClass("hidden")
  } else {
    $(".difference").addClass("hidden")
  }
})

function check_unlock() {
  response_log.every(r => r != "") ? $("#button_next").removeAttr("disabled") : $("#button_next").attr("disabled", "disabled")
}


async function load_next() {
  let data = await get_next_pair()

  response_log = data.src.map(_ => "")

  let html_new = ""
  for (let i = 0; i < data.src.length; i++) {
    html_new += `
    <div class="output">${data.out_a[i]}</div>
    <div class="output">${data.src[i]}</div>
    <div class="output">${data.out_b[i]}</div>
    <br>
    <div class="button_panel">
    <input type="button" i="${i}" class="button_left     button_navigation" value="left better">
    <input type="button" i="${i}" class="button_bothbad  button_navigation" value="both bad">
    <input type="button" i="${i}" class="button_bothgood button_navigation" value="both fine">
    <input type="button" i="${i}" class="button_right    button_navigation" value="right better">
    </div>
    <br>
    <br>
    `
  }

  $("#output_div").html(html_new)

  // make sure the event loop passes
  await new Promise(r => setTimeout(r, 0));
  check_unlock()

  $(".button_left,.button_right,.button_bothbad,.button_bothgood").on("click", function() {
    $(this).parent().find(".button_navigation").removeClass("button_selected")
    $(this).addClass("button_selected")

    let i = parseInt($(this).attr("i")!)
    if ($(this).hasClass("button_left")) {
      response_log[i] = "left"
    } else if ($(this).hasClass("button_right")) {
      response_log[i] = "right"
    } else if ($(this).hasClass("button_bothbad")) {
      response_log[i] = "bothbad"
    } else if ($(this).hasClass("button_bothgood")) {
      response_log[i] = "bothgood"
    } else {
      console.error("unknown button class")
    }

    check_unlock()
  })
}

$("#button_next").attr("disabled", "disabled")

$("#button_next").on("click", function() {
  load_next()
})

load_next()