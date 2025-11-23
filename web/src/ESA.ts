import $ from 'jquery';
import { get_next_item, Item } from './connector';
let response_log: Array<any> = []

$("#toggle_differences").on("change", function() {
  if ($(this).is(":checked")) {
    $(".difference").removeClass("hidden")
  } else {
    $(".difference").addClass("hidden")
  }
})

function check_unlock() {
  response_log.every(r => r != null) ? $("#button_next").removeAttr("disabled") : $("#button_next").attr("disabled", "disabled")
}


async function load_next() {
  let data = await get_next_item()

  response_log = data.src.map(_ => null)

  let html_new = ""
  for (let i = 0; i < data.src.length; i++) {
    html_new += `
    <div class="output_block">
    <span class="language_indicator">??</span>
    <div class="output_srctgt">
      <div class="output_src">${data.src[i]}</div>
      <div class="output_tgt">${data.tgt[i]}</div>
    </div>
    <div class="output_response">
      <input type="range" min="0" max="100" value="-1" id="response_${i}" orient="vertical">
      <br>
      <label class="output_number">?</label>
    </div>
    <div class="output_labels">
      100: perfect
      <br>
      <br>
      <br>
      66: middling
      <br>
      <br>
      <br>
      33: broken
      <br>
      <br>
      <br>
      0: nonsense
      
    </div>
    </div>
    `
  }

  $("#output_div").html(html_new)

  // make sure the event loop passes
  await new Promise(r => setTimeout(r, 0));
  check_unlock()

  $(".output_block").each((_, self) => {
    let slider = $(self).find("input[type='range']")
    let label = $(self).find(".output_number")
    slider.on("input", function() {
      let val = parseInt((<HTMLInputElement> this).value)
      label.text(val.toString())
      let i = parseInt(slider.attr("id")!.split("_")[1])
      response_log[i] = val
      check_unlock()
    })
  })

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