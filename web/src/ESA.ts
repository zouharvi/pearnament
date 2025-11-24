import $ from 'jquery';
import { get_next_item, log_response } from './connector';
let response_log: Array<any> = []
let action_log: Array<any> = []

$("#toggle_differences").on("change", function () {
  if ($(this).is(":checked")) {
    $(".difference").removeClass("hidden")
  } else {
    $(".difference").addClass("hidden")
  }
})

function check_unlock() {
  if (response_log.every(r => r != null)) {
    $("#button_next").removeAttr("disabled")
    $("#button_next").val("Next ✅")
  } else {
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 🚧")
  }
}

export type DataPayload = { "status": string, "progress": { "completed": number, "total": number, "time": number }, "payload": { "src": Array<string>, "tgt": Array<string> }, }
export type DataFinished = { "status": string, "progress": { "completed": number, "total": number, "time": number,  }, "token": string,  }

async function display_next(response: DataPayload) {
  $("#progress").text(`Progress: ${response.progress.completed}/${response.progress.total}`)
  $("#time").text(`Annotation time: ${Math.round(response.progress.time/60)}m`)

  let data = response.payload
  response_log = data.src.map(_ => null)
  action_log = [{ "time": Date.now()/1000, "action": "load" }]

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
    slider.on("input", function () {
      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
      let i = parseInt(slider.attr("id")!.split("_")[1])
      response_log[i] = val
      check_unlock()
      action_log.push({ "time": Date.now()/1000, "index": i, "value": val })
    })
  })

  $(".button_left,.button_right,.button_bothbad,.button_bothgood").on("click", function () {
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


async function load_next() {
  let response = await get_next_item<DataPayload | DataFinished>()

  if (response.status == "completed") {
    let response_finished = response as DataFinished
    $("#output_div").html(`
    <div class='white-box' style='width: max-content'>
    <h2>🎉 All done, thank you for your annotations!</h2>

    If someone asks you for a token of completion, show them:
    <span style="font-family: monospace; font-size: 11pt;">${response_finished.token}</span>
    <br>
    <br>
    </div>
    `)
    $("#progress").text(`Progress: ${response.progress.completed}/${response.progress.total}`)
    $("#time").text(`Total annotation time: ${Math.round(response_finished.progress.time/60)}m`)
    $("#button_next").hide()
  } else if (response.status == "ok") {
    display_next(response as DataPayload)
  } else {
    console.error("Non-ok response", response)
  }
}

$("#button_next").on("click", async function () {
  // disable while communicating with the server
  $("#button_next").attr("disabled", "disabled")
  $("#button_next").val("Next 📶")
  action_log.push({ "time": Date.now()/1000, "action": "submit" })
  await log_response({"annotations": response_log, "actions": action_log})
  await load_next()
})

load_next()